# -*- coding: utf-8 -*-
"""半自动放兵流程：读 out/marks/marks.json 的 steps，逐条执行/记录。

用法：
    python -m clashlab.autoplay [--dry-run] [--marks PATH] [--channel auto]
                                [--serial 127.0.0.1:5555] [--wait-ms 1500]

- --dry-run：只写日志不下发点击。
- ESC 随时中断：立即停止后续点击并安全退出。
- 进攻（首次下兵）前留 1 秒可中断窗口。
- adb 掉线/雷电关闭不抛未捕获异常，记日志后安全退出。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import threading
import time
from typing import List, Optional

from .touch import LdTouch, OVERLAY_DIR, _iso
from .geo import Calib

# 实测 quad（1280x720 真实村庄帧）
DEFAULT_QUAD = [[697, 107], [944, 351], [672, 585], [347, 327]]

# 动作类步骤关键词（下兵/放英雄/技能）；其余为说明性步骤，只记录不下发
ACTION_VERBS = ("下", "放", "顶前", "殿后", "切入", "开书", "滚", "部署", "投放")
NOTE_MARKERS = ("未知", "避开", "不假设", "留一发", "陷阱位置", "装备未知")

ESC_VK = 0x1B

MONITORINFOF_PRIMARY = 0x00000001


def _primary_monitor_probe() -> dict:
    """启动守卫：枚举 LDPlayerMainFrame 子窗找 RenderWindow，MonitorFromWindow + GetMonitorInfo
    判断其是否落在主显示器。返回 {primary, monitor, device, rc_monitor, found}。"""
    import win32api, win32gui, win32con
    out = {"primary": False, "found": False, "monitor": None, "device": None,
           "rc_monitor": None, "monitors": None, "error": None}
    try:
        out["monitors"] = len(win32api.EnumDisplayMonitors())
    except Exception:
        out["monitors"] = -1
    render_hwnd = None
    def _cb_main(hwnd, _):
        nonlocal render_hwnd
        if render_hwnd is not None:
            return True
        if win32gui.GetClassName(hwnd) != "LDPlayerMainFrame":
            return True
        kids = []
        win32gui.EnumChildWindows(hwnd, lambda ch, _: kids.append(ch) or True, None)
        for ch in kids:
            if win32gui.GetClassName(ch) == "RenderWindow":
                render_hwnd = ch
                break
        return True
    win32gui.EnumWindows(_cb_main, None)
    if render_hwnd is None:
        out["error"] = "render window not found"
        return out
    out["found"] = True
    try:
        mon = win32api.MonitorFromWindow(render_hwnd, win32con.MONITOR_DEFAULTTONEAREST)
        info = win32api.GetMonitorInfo(mon)
        out["monitor"] = hex(int(mon))
        out["device"] = info.get("Device")
        out["rc_monitor"] = list(info.get("Monitor", ()))
        out["primary"] = bool(info.get("Flags", 0) & MONITORINFOF_PRIMARY)
    except Exception as e:
        out["error"] = f"probe failed: {e}"
    return out


class _EscWatcher(threading.Thread):
    """后台轮询 ESC，按下即置 stop 标志。"""

    def __init__(self):
        super().__init__(daemon=True)
        self.stop = False
        self._run = True

    def run(self):
        import ctypes
        while self._run and not self.stop:
            # 0x8000 位表示自上次调用后按下
            if ctypes.windll.user32.GetAsyncKeyState(ESC_VK) & 0x8000:
                self.stop = True
                break
            time.sleep(0.05)

    def shutdown(self):
        self._run = False


def parse_step_coords(text: str) -> List[tuple]:
    out = []
    for m in re.finditer(r"\((\d{1,2})\s*,\s*(\d{1,2})\)", text):
        out.append((int(m.group(1)), int(m.group(2))))
    return out


def classify_step(text: str) -> str:
    if any(k in text for k in NOTE_MARKERS) and not any(v in text for v in ("下", "放")):
        return "note"
    if any(v in text for v in ACTION_VERBS):
        return "action"
    return "note"


def log_line(msg: str, log_path: Optional[str] = None) -> None:
    line = f"{_iso()} [autoplay] {msg}"
    print(line, flush=True)
    if log_path:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def run(marks_path: str, dry_run: bool = False, channel: str = "auto",
        serial: str = "127.0.0.1:5555", wait_ms: int = 1500,
        out_dir: str = OVERLAY_DIR, allow_primary: bool = False) -> dict:
    log_path = os.path.join(out_dir, "autoplay.log")
    result = {"steps_total": 0, "steps_action": 0, "steps_note": 0,
              "clicked": 0, "failed": 0, "interrupted": False, "dry_run": dry_run,
              "refused": False}

    # 主屏禁区守卫（默认硬拒绝，不等待、不先跑几步）：渲染窗在主显示器即退出
    if not allow_primary:
        chk = _primary_monitor_probe()
        if chk.get("primary"):
            msg = (f"PRIMARY-GUARD: render window on primary display "
                   f"(device={chk.get('device')} rc_monitor={chk.get('rc_monitor')} "
                   f"monitor={chk.get('monitor')} monitors={chk.get('monitors')}); "
                   f"refuse to run. "
                   f"action=connect secondary display | move LDPlayer inside (0,0)-(1920,1080) | "
                   f"--allow-primary(not recommended)")
            log_line("FATAL " + msg, log_path)
            return {**result, "refused": True, "error": msg}
        if chk.get("error") and not chk.get("found"):
            log_line(f"WARN primary guard probe: {chk['error']}（未找到渲染窗，按无雷电处理继续）", log_path)

    # 读 marks
    try:
        with open(marks_path, "r", encoding="utf-8") as f:
            marks = json.load(f)
    except Exception as e:
        log_line(f"FATAL 读取 marks.json 失败: {e}", log_path)
        return {**result, "error": f"marks read: {e}"}

    steps = marks.get("steps", [])
    result["steps_total"] = len(steps)
    log_line(f"加载 marks={marks_path} steps={len(steps)} dry_run={dry_run} channel={channel}", log_path)

    # 几何：quad -> Calib（格->px 唯一入口 geo.Calib）
    try:
        calib = Calib.from_quad(DEFAULT_QUAD)
    except Exception as e:
        log_line(f"WARN Calib 构造失败，坐标按原值下发: {e}", log_path)
        calib = None

    ld = LdTouch(live=not dry_run, adb_serial=serial)
    watcher = _EscWatcher()
    watcher.start()

    executed_any = False
    try:
        for idx, text in enumerate(steps, 1):
            if watcher.stop:
                result["interrupted"] = True
                log_line("ESC 中断：停止后续步骤", log_path)
                break
            kind = classify_step(text)
            coords = parse_step_coords(text)
            log_line(f"步骤{idx}/{len(steps)} [{kind}] {text}", log_path)

            if kind != "action":
                log_line(f"步骤{idx} 说明性步骤，不下发", log_path)
                result["steps_note"] += 1
                continue

            result["steps_action"] += 1

            # 首次动作前留 1 秒可中断窗口
            if not executed_any:
                log_line("进攻开始前 1 秒中断窗口（按 ESC 取消）...", log_path)
                for _ in range(10):
                    if watcher.stop:
                        result["interrupted"] = True
                        log_line("ESC 中断于进攻前窗口", log_path)
                        return {**result, "interrupted": True}
                    time.sleep(0.1)
                executed_any = True

            for gx, gy in coords:
                if watcher.stop:
                    result["interrupted"] = True
                    log_line("ESC 中断：停止后续点击", log_path)
                    break
                try:
                    if calib is not None:
                        px, py = calib.tile_to_px(gx, gy)
                    else:
                        px, py = float(gx), float(gy)
                    res = ld.click_render_xy(px, py, method=channel,
                                              semantic=f"step{idx}:tile({gx},{gy})",
                                              seq="autoplay")
                    if res.get("ok") or res.get("dry_run"):
                        result["clicked"] += 1
                        log_line(f"步骤{idx} 下发 tile({gx},{gy}) -> render({px:.1f},{py:.1f}) ok={res.get('ok')} {res.get('method')}", log_path)
                    else:
                        result["failed"] += 1
                        log_line(f"步骤{idx} 下发失败: {res.get('errors')}", log_path)
                except Exception as e:
                    result["failed"] += 1
                    log_line(f"步骤{idx} 异常（不崩溃，继续）: {e}", log_path)
            time.sleep(wait_ms / 1000.0)
    finally:
        watcher.shutdown()
        ld.close()

    log_line(f"结束 clicked={result['clicked']} failed={result['failed']} interrupted={result['interrupted']}", log_path)
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description="半自动放兵（marks.json steps）")
    ap.add_argument("--dry-run", action="store_true", help="只写日志不点击")
    default_marks = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "out", "marks", "marks.json")
    ap.add_argument("--marks", default=default_marks)
    ap.add_argument("--channel", default="auto", choices=["auto", "mouse_sendinput", "mouse_postmsg", "adb"])
    ap.add_argument("--serial", default="127.0.0.1:5555")
    ap.add_argument("--wait-ms", type=int, default=1500)
    ap.add_argument("--allow-primary", action="store_true",
                    help="逃生开关（不建议）：允许渲染窗在主显示器时运行；默认硬拒绝")
    args = ap.parse_args(argv)
    res = run(args.marks, dry_run=args.dry_run, channel=args.channel,
              serial=args.serial, wait_ms=args.wait_ms, allow_primary=args.allow_primary)
    print(json.dumps(res, ensure_ascii=False, indent=1))
    if res.get("refused"):
        return 2
    return 0 if res.get("failed", 0) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
