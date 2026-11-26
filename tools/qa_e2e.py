#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""实机端到端 UI/绘制 QA 矩阵（单命令复跑）。

覆盖：
  1) HUD 启动（无 layouts/layout_current.json）
  2) HUD 启动（有 layouts/layout_current.json，临时写入/结束恢复）
  3) PANEL 启动（无布局）
  4) PANEL 启动（有布局）
  5) PANEL 研究页 -> 阵型页（进程内注入 ImGui 页签点击，走真实按钮->set_page 路径）
  6) HUD 运行中改 LDPlayer 窗口尺寸（缩小再还原），核对自动重标定日志
  7) dist/ClashOverlay.exe --seconds 6 --no-show 自检

产物：out/qa_e2e/*.png、out/qa_e2e/logs/*.stdout.log、out/qa_e2e/summary.json
用法：D:\Python313\python.exe tools\qa_e2e.py [--only CASE] [--duration SEC]

注意：不改产品代码；只临时改 layouts/layout_current.json，结束按原状恢复/删除。
OS 级鼠标注入在本机被冻结（SetCursorPos/SendInput 无效），页签点击改为在
overlay 进程内把 ImGui 事件喂给真实的 pages._tab_row 按钮，属同一条 UI 代码路径。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out" / "qa_e2e"
LOGDIR = OUT / "logs"
LAYOUT_CURRENT = ROOT / "layouts" / "layout_current.json"
LAYOUT_SAMPLE = ROOT / "layouts" / "th13_sample.json"
EXE = ROOT / "dist" / "ClashOverlay.exe"
PY = sys.executable or r"D:\Python313\python.exe"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1", PYTHONUTF8="1")

PAGE_HARNESS = r'''
import os, sys, time
root = sys.argv[1]; target_page = sys.argv[2]; runsec = float(sys.argv[3])
sys.path.insert(0, root); os.chdir(root)
from clashlab.overlay import runtime as R
import win32gui
_s = {"n": 0, "done": False}
def feed(rt, window, hwnd, io, prev):
    # 本机 OS 光标注入被冻结：只在本进程内喂 ImGui 事件；不调用真实 GetCursorPos 通路，
    # 否则真实 (-1,-1)/窗外事件会覆盖注入点。按钮仍是 pages._tab_row 的 imgui.button。
    _s["n"] += 1
    n = _s["n"]
    if n < 20:
        return
    l, tp, r, b = win32gui.GetWindowRect(hwnd)
    W = r - l
    panel_w = 440 if W > 480 else W
    px = (W - panel_w) if W > 480 else 0
    bw = (panel_w - 28 - 24) / 4.0
    x = px + 14 + 1 * (bw + 8) + bw / 2.0   # 第 2 个页签“阵型”
    y = 12 + 13
    io.add_mouse_pos_event(float(x), float(y))
    io.add_mouse_button_event(0, 100 <= n < 106)
    if n == 40:
        rt.log("QA harness: armed (hovering tab, research visible)")
    if n == 100:
        rt.log(f"QA harness: inject tab click -> {target_page} at ({x:.1f},{y:.1f})")
    if n == 140 and not _s["done"]:
        _s["done"] = True
        rt.log(f"QA harness: state.page={rt.state.page} (wanted {target_page})")
R._feed_panel_mouse = feed
R.run(root, {"show": True, "mode": "PANEL", "always_on_top": True,
             "allow_primary": True, "run_seconds": runsec})
'''


def _wg():
    import win32gui
    return win32gui


def screen_bbox():
    import ctypes
    u = ctypes.windll.user32
    return (u.GetSystemMetrics(76), u.GetSystemMetrics(77),
            u.GetSystemMetrics(78), u.GetSystemMetrics(79))


def find_target():
    """与 clashlab.overlay.runtime.find_render_target 同口径：最后一个可见
    LDPlayerMainFrame，再取其中可见客户区面积最大的子窗口。"""
    wg = _wg()
    main = [None]

    def cb(h, _):
        if wg.GetClassName(h) == "LDPlayerMainFrame" and wg.IsWindowVisible(h):
            main[0] = h

    wg.EnumWindows(cb, None)
    if not main[0]:
        return None, None
    best = [None, 0]

    def walk(h):
        kids = []
        wg.EnumChildWindows(h, lambda k, _: kids.append(k) or True, None)
        for k in kids:
            if wg.IsWindowVisible(k):
                r = wg.GetClientRect(k)
                area = r[2] * r[3]
                if area > best[1]:
                    best[0], best[1] = k, area
                    walk(k)

    walk(main[0])
    return main[0], best[0]


def client_screen_rect(child):
    wg = _wg()
    pt = wg.ClientToScreen(child, (0, 0))
    r = wg.GetClientRect(child)
    return (pt[0], pt[1], pt[0] + r[2], pt[1] + r[3])


def grab_full():
    from PIL import ImageGrab
    return ImageGrab.grab(all_screens=True)


def crop_save(full, rect, name):
    vx, vy, _, _ = screen_bbox()
    l, t, r, b = [int(v) for v in rect]
    box = (max(0, l - vx), max(0, t - vy),
           min(full.width, r - vx), min(full.height, b - vy))
    img = full.crop(box)
    path = OUT / name
    img.save(path)
    return path, img


def parse_rect(lines, mode):
    pat = re.compile(r"mode=%s rect=\((\d+),(\d+),(\d+)x(\d+)\)" % re.escape(mode))
    for ln in reversed(lines):
        m = pat.search(ln)
        if m:
            x, y, w, h = (int(v) for v in m.groups())
            return (x, y, x + w, y + h)
    return None


def wait_line(lines, needle, timeout):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if any(needle in ln for ln in lines):
            return True
        time.sleep(0.05)
    return False


def set_layout(enabled):
    LAYOUT_CURRENT.parent.mkdir(parents=True, exist_ok=True)
    if enabled:
        LAYOUT_CURRENT.write_bytes(LAYOUT_SAMPLE.read_bytes())
    else:
        if LAYOUT_CURRENT.exists():
            LAYOUT_CURRENT.unlink()


def restore_layout(orig_bytes):
    if orig_bytes is None:
        if LAYOUT_CURRENT.exists():
            LAYOUT_CURRENT.unlink()
    else:
        LAYOUT_CURRENT.parent.mkdir(parents=True, exist_ok=True)
        LAYOUT_CURRENT.write_bytes(orig_bytes)


def spawn(cmd, tag):
    p = subprocess.Popen(cmd, cwd=str(ROOT), env=ENV, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, encoding="utf-8",
                         errors="replace")
    lines, errs = [], []
    lock = threading.Lock()

    def rd(stream, dst):
        for ln in stream:
            with lock:
                dst.append(ln.rstrip("\r\n"))

    t1 = threading.Thread(target=rd, args=(p.stdout, lines), daemon=True)
    t2 = threading.Thread(target=rd, args=(p.stderr, errs), daemon=True)
    t1.start(); t2.start()
    logfile = LOGDIR / (tag + ".stdout.log")
    return p, lines, errs, (t1, t2), logfile


def finish_proc(p, threads, lines, errs, logfile, timeout):
    timed_out = False
    code = None
    try:
        code = p.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        p.kill()
        try:
            code = p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            code = None
    for t in threads:
        t.join(timeout=2)
    try:
        logfile.write_text("\n".join(lines + ["--- STDERR ---"] + errs), encoding="utf-8")
    except Exception:
        pass
    return code, timed_out


def key_lines(lines, needles, limit=10):
    out = []
    for ln in lines:
        if any(n in ln for n in needles):
            out.append(ln.strip())
            if len(out) >= limit:
                break
    return out


def bad_lines(lines):
    pats = ("Traceback", "draw frame error", "calib build fail", "MISMATCH",
            "recalib error", "overlay runtime start failed")
    return [ln.strip() for ln in lines if any(p in ln for p in pats)]


def diff_pct(path_a, path_b, step=2):
    from PIL import Image
    a = Image.open(path_a).convert("RGB")
    b = Image.open(path_b).convert("RGB")
    if a.size != b.size:
        return None
    pa, pb = a.load(), b.load()
    n = 0
    total = 0
    for y in range(0, a.size[1], step):
        for x in range(0, a.size[0], step):
            total += 1
            ca, cb = pa[x, y], pb[x, y]
            if max(abs(ca[0] - cb[0]), abs(ca[1] - cb[1]), abs(ca[2] - cb[2])) > 8:
                n += 1
    return round(100.0 * n / max(total, 1), 2)


def case_visible(cid, title, mode, layout, duration, resize=False, page=False):
    set_layout(layout)
    result = {
        "id": cid, "title": title, "mode": mode, "layout": layout,
        "shots": [], "key_lines": [], "notes": [], "result": "FAIL",
        "cmd": "", "exit": None, "diff": {},
    }
    main, child = find_target()
    if not main or not child:
        result["notes"].append("未找到 LDPlayerMainFrame/RenderWindow")
        return result
    rect = client_screen_rect(child)
    if page:
        cmd = [PY, "-c", PAGE_HARNESS, str(ROOT), "layout", str(duration)]
        result["cmd"] = ("python -c <QA_PAGE_HARNESS> " + str(ROOT) +
                         " layout " + str(duration) +
                         "  （内部 runtime.run；注入页签点击）")
    else:
        cmd = [PY, "run_overlay.py", "--show", "--mode", mode,
               "--always-on-top", "--allow-primary", "--run-seconds", str(duration)]
        result["cmd"] = ("python run_overlay.py --show --mode %s --always-on-top "
                         "--allow-primary --run-seconds %s" % (mode, duration))
    p, lines, errs, threads, logfile = spawn(cmd, cid)
    try:
        if page:
            if not wait_line(lines, "mode=PANEL rect=", 20):
                result["notes"].append("PANEL 窗口未出现（等待 mode=PANEL rect 超时）")
            if not wait_line(lines, "QA harness: armed", 20):
                result["notes"].append("harness armed 未出现")
            time.sleep(0.15)
            full = grab_full()
            prect = parse_rect(lines, "PANEL") or rect
            p1, _ = crop_save(full, prect, cid + "_research.png")
            result["shots"].append(str(p1.relative_to(ROOT)))
            if wait_line(lines, "QA harness: inject tab click", 20):
                time.sleep(0.8)
                full = grab_full()
                p2, _ = crop_save(full, prect, cid + "_layout.png")
                result["shots"].append(str(p2.relative_to(ROOT)))
                if p1.exists() and p2.exists():
                    result["diff"]["research_vs_layout_pct"] = diff_pct(p1, p2)
            else:
                result["notes"].append("页签点击注入未发生")
        else:
            if not wait_line(lines, "mode=%s rect=" % mode, 20):
                result["notes"].append("覆盖层窗口未出现（等待 mode=%s rect 超时）" % mode)
            time.sleep(0.8)
            full = grab_full()
            rect2 = parse_rect(lines, mode) or rect
            if cid == "hud_nolayout":
                full_path = OUT / (cid + "_desktop.png")
                full.save(full_path)
                result["shots"].append(str(full_path.relative_to(ROOT)))
            shot, _ = crop_save(full, rect2, cid + ".png")
            result["shots"].append(str(shot.relative_to(ROOT)))
            if resize:
                wg = _wg()
                orig = wg.GetWindowRect(main)
                result["main_rect_orig"] = list(orig)
                try:
                    wg.SetWindowPos(main, 0, orig[0], orig[1],
                                    orig[2] - orig[0] - 140, orig[3] - orig[1] - 90,
                                    0x0002 | 0x0004)
                    time.sleep(1.6)
                    full = grab_full()
                    m2, c2 = find_target()
                    r2 = client_screen_rect(c2) if c2 else rect2
                    shot2, _ = crop_save(full, r2, cid + "_shrunk.png")
                    result["shots"].append(str(shot2.relative_to(ROOT)))
                finally:
                    wg.SetWindowPos(main, 0, orig[0], orig[1],
                                    orig[2] - orig[0], orig[3] - orig[1],
                                    0x0002 | 0x0004)
                time.sleep(1.6)
                full = grab_full()
                m3, c3 = find_target()
                r3 = client_screen_rect(c3) if c3 else rect2
                shot3, _ = crop_save(full, r3, cid + "_restored.png")
                result["shots"].append(str(shot3.relative_to(ROOT)))
                result["main_rect_restored"] = list(wg.GetWindowRect(main))
                result["rects"] = {"normal": list(rect2), "shrunk": list(r2), "restored": list(r3)}
    finally:
        code, timed_out = finish_proc(p, threads, lines, errs, logfile, duration + 30)
        result["exit"] = code
        if timed_out:
            result["notes"].append("进程超时被 kill")

    need = ["overlay runtime start", "overlay loop start", "fps summary", "overlay runtime end"]
    if page:
        need += ["QA harness: inject tab click", "QA harness: state.page=layout"]
    if mode == "HUD":
        need += ["start_mode=HUD", "mode=HUD rect="]
    else:
        need += ["start_mode=PANEL", "mode=PANEL rect="]
    missing = [n for n in need if not any(n in ln for ln in lines)]
    bad = bad_lines(lines)
    keys = ["overlay loop start", "overlay SHOW", "mode=%s rect=" % mode,
            "PANEL draw container first frame", "QA harness: inject tab click",
            "QA harness: state.page=", "viewport", "recalib", "fps summary"]

    if resize:
        if not any(re.search(r"viewport \d+x\d+ -> \d+x\d+", ln) for ln in lines):
            missing.append("viewport ... -> ...; calib rebuilt")
        for n in ("viewport 变化 >10%", "recalib: view_quads table adopted"):
            if not any(n in ln for ln in lines):
                missing.append(n)
        if result.get("main_rect_restored") != result.get("main_rect_orig"):
            result["notes"].append("窗口尺寸未还原: %r != %r" % (result.get("main_rect_restored"), result.get("main_rect_orig")))
    if page:
        d = result["diff"].get("research_vs_layout_pct")
        if d is None or d < 1.0:
            result["notes"].append("研究页/阵型页截图差异过小: %r" % d)
    result["key_lines"] = key_lines(lines, keys)
    shots_ok = all((ROOT / s).exists() and (ROOT / s).stat().st_size > 5000 for s in result["shots"])
    if not shots_ok:
        result["notes"].append("截图缺失或过小")
    result["result"] = ("PASS" if (code == 0 and not missing and not bad and shots_ok)
                        else "FAIL")
    if missing:
        result["notes"].append("缺少关键日志: " + "; ".join(missing))
    if bad:
        result["notes"].append("错误行: " + "; ".join(bad[:3]))
    result["log_tail"] = lines[-15:] if result["result"] != "PASS" else lines[-4:]
    return result


def case_exe(duration=6):
    result = {"id": "exe_selfcheck", "title": "dist/ClashOverlay.exe --seconds 6 --no-show",
              "shots": [], "key_lines": [], "notes": [], "result": "FAIL", "exit": None,
              "cmd": "dist\\ClashOverlay.exe --seconds 6 --no-show"}
    if not EXE.exists():
        result["notes"].append("dist\\ClashOverlay.exe 不存在")
        return result
    logp = ROOT / "out" / "overlay" / "overlay.log"
    before = logp.stat().st_size if logp.exists() else 0
    t0 = time.time()
    p = subprocess.Popen([str(EXE), "--seconds", str(duration), "--no-show"],
                         cwd=str(ROOT), env=ENV)
    shot = None
    time.sleep(4.0)
    try:
        full = grab_full()
        shot = OUT / "exe_selfcheck_desktop.png"
        full.save(shot)
        result["shots"].append(str(shot.relative_to(ROOT)))
    except Exception as e:
        result["notes"].append("桌面截图失败: %r" % (e,))
    try:
        code = p.wait(timeout=120)
    except subprocess.TimeoutExpired:
        p.kill(); code = p.wait(10)
        result["notes"].append("exe 自检超时被 kill")
    result["exit"] = code
    appended = ""
    if logp.exists():
        with open(logp, "rb") as f:
            f.seek(before)
            appended = f.read().decode("utf-8", "replace")
    result["log_append"] = appended
    need = ["self-check mode (invisible) start", "self-check done in", "marks keys="]
    missing = [n for n in need if n not in appended]
    wg = _wg()
    win = [None]

    def cb(h, _):
        if wg.IsWindowVisible(h) and "ClashOverlay" in (wg.GetWindowText(h) or ""):
            win[0] = h

    wg.EnumWindows(cb, None)
    result["visible_overlay_window"] = bool(win[0])
    result["key_lines"] = [ln.strip() for ln in appended.splitlines()
                           if any(k in ln for k in ("self-check", "marks keys", "calib tile"))][:8]
    result["notes"].append("exe 为 console=False，无 stdout；证据为 out/overlay/overlay.log 增量")
    ok = code == 0 and not missing and shot is not None and not win[0]
    result["result"] = "PASS" if ok else "FAIL"
    if missing:
        result["notes"].append("缺少日志: " + "; ".join(missing))
    result["log_tail"] = appended.splitlines()[-8:] if result["result"] != "PASS" else appended.splitlines()[-3:]
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="只跑某个 case id（逗号分隔）")
    ap.add_argument("--duration", type=float, default=None, help="覆盖可见用例秒数")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    LOGDIR.mkdir(parents=True, exist_ok=True)
    if not LAYOUT_SAMPLE.exists():
        print("FAIL: 缺少布局样本", LAYOUT_SAMPLE)
        return 2
    orig = LAYOUT_CURRENT.read_bytes() if LAYOUT_CURRENT.exists() else None
    results = []
    try:
        specs = [
            ("hud_nolayout", "HUD（无 layout_current）", "HUD", False, 8, False, False),
            ("hud_layout", "HUD（有 layout_current）", "HUD", True, 8, False, False),
            ("panel_nolayout", "PANEL（无布局）", "PANEL", False, 8, False, False),
            ("panel_layout", "PANEL（有布局）", "PANEL", True, 8, False, False),
            ("panel_page", "PANEL 研究页 -> 阵型页", "PANEL", True, 9, False, True),
            ("hud_resize", "HUD 运行中缩小窗口再还原", "HUD", False, 12, True, False),
        ]
        only = set(x.strip() for x in args.only.split(",") if x.strip())
        for cid, title, mode, layout, dur, resize, page in specs:
            if only and cid not in only:
                continue
            print("RUN", cid, "...", flush=True)
            results.append(case_visible(cid, title, mode, layout,
                                        args.duration or dur, resize, page))
        if not only or "exe_selfcheck" in only:
            print("RUN exe_selfcheck ...", flush=True)
            results.append(case_exe(6))
    finally:
        restore_layout(orig)

    # 面板布局有无的差异（补充证据）
    pl = OUT / "panel_layout.png"
    pn = OUT / "panel_nolayout.png"
    if pl.exists() and pn.exists():
        d = diff_pct(pn, pl)
        for r in results:
            if r["id"] == "panel_layout":
                r["diff"]["vs_panel_nolayout_pct"] = d
    hl = OUT / "hud_layout.png"
    hn = OUT / "hud_nolayout.png"
    if hl.exists() and hn.exists():
        d = diff_pct(hn, hl)
        for r in results:
            if r["id"] == "hud_layout":
                r["diff"]["vs_hud_nolayout_pct"] = d

    summary = {"root": str(ROOT), "python": PY, "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
               "layout_original_present": orig is not None,
               "layout_restored": (LAYOUT_CURRENT.read_bytes() == orig) if (orig is not None and LAYOUT_CURRENT.exists()) else (orig is None and not LAYOUT_CURRENT.exists()),
               "cases": results}
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n== QA E2E 汇总 ==")
    ok = 0
    for r in results:
        shots = []
        for s in r["shots"]:
            p = ROOT / s
            shots.append("%s (%d B)" % (Path(s).name, p.stat().st_size if p.exists() else -1))
        print("[%s] %-14s exit=%s shots=%s" % (r["result"], r["id"], r["exit"], ", ".join(shots)))
        for ln in r["key_lines"][:4]:
            print("        log:", ln[:150])
        for n in r["notes"]:
            print("        note:", n)
        for k, v in (r.get("diff") or {}).items():
            print("        diff:", k, "=", v, "%")
        if r["result"] == "PASS":
            ok += 1
        elif r.get("log_tail"):
            print("        tail:", " | ".join(x[-160:] for x in r["log_tail"][-3:]))
    print("\nPASS %d / FAIL %d / total %d" % (ok, len(results) - ok, len(results)))
    print("summary:", OUT / "summary.json")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
