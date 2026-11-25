# -*- coding: utf-8 -*-
"""覆盖层 PANEL UI 冒烟脚本（只开 A 的覆盖层窗口，不另建窗口）。

用法：
  静态阶段（默认，无需可见模式）：
    D:\\Python313\\python.exe tools\\overlay_ui_smoke.py
  可见阶段（A 运行时收尾后重跑；需雷电在前台、桌面锁规则遵守）：
    D:\\Python313\\python.exe tools\\overlay_ui_smoke.py --live --seconds 25

静态阶段：import 全模块 + 纯逻辑断言（模型播种/命中/冻结/往返），
结果写 out/overlay/ui_smoke.log，不开窗。
可见阶段：
  1. 子进程启动 run_overlay.py --show --mode PANEL（A 的唯一窗口）；
  2. 等 clashlab-overlay 窗口出现；
  3. 逐页截图 out/overlay/ui_research.png / ui_collect.png / ui_setting.png；
  4. 鼠标点一次「冻结 layout」、点一次候选框拖动（best-effort 坐标）；
  5. 全部结果写 ui_smoke.log。
可见环境不具备（无雷电/窗口未出现）时记 SKIP，不报错退出。
"""
import argparse
import inspect
import json
import os
import subprocess
import sys
import time
import traceback

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, ROOT)

LOG_PATH = os.path.join(ROOT, "out", "overlay", "ui_smoke.log")
LINES = []


def log(msg):
    LINES.append(msg)
    print(msg)


def check(name, ok, detail=""):
    log(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")
    return bool(ok)


# ================================================================ 静态阶段

def static_phase():
    log("== static phase ==")
    from clashlab.overlay import data, editor, pages
    from clashlab.geo import Calib

    check("pages import 无副作用", True)
    sig = inspect.signature(pages.draw_panel)
    check("draw_panel(ctx, state) 两参签名", list(sig.parameters) == ["ctx", "state"])

    # 模型播种（模拟 state.candidates）
    model = editor.EditorModel([
        {"id": "c0", "label": "air-defense", "bbox": [300, 200, 360, 260],
         "confidence": 0.61},
        {"id": "c1", "label": "scattershot", "bbox": [500, 300, 570, 370],
         "confidence": 0.93},
    ], calib=Calib.from_quad([[697, 107], [944, 351], [672, 585], [347, 327]]))
    check("模型播种 2 候选", len(model.candidates) == 2)

    cid, part = model.hit_test(330, 230, 8.0)
    check("命中 c0 体内", cid == "c0" and part == "body", f"hit=({cid},{part})")
    model.begin_drag(330, 230, 8.0)
    model.drag_to(350, 250)
    model.end_drag()
    check("拖动生效", model.get("c0")["bbox"][0] == 320.0)

    # 视图变换往返
    vt = editor.ViewTransform(1280, 720, ax=12, ay=196, aw=396, ah=218)
    mx, my = vt.render_to_panel(330, 230)
    rx, ry = vt.panel_to_render(mx, my)
    err = ((rx - 330) ** 2 + (ry - 230) ** 2) ** 0.5
    check("panel<->render 往返 <1px", err < 1.0, f"err={err:.6f}px")

    # 冻结（临时目录，不写业务 layouts/）
    import tempfile
    res = editor.freeze_layout(model, tempfile.mkdtemp(),
                               source_meta={"image": "overlay.png"},
                               quad=[[697, 107], [944, 351], [672, 585], [347, 327]],
                               clock=lambda f: "20260101_000000" if f == "%Y%m%d_%H%M%S" else "2026-01-01T00:00:00")
    check("冻结 ok", res["ok"], res["message"])
    check("冻结 schema 无错", res["errors"] == [])

    # 数据层真实文件探测（缺文件不崩）
    paths = data.Paths(ROOT)
    view = data.load_panel_view(paths)
    check("load_panel_view 不崩", isinstance(view, dict) and "candidates" in view)
    anchors = data.load_anchors(paths)["anchors"]
    check("锚点表 10 条（8 已验证）", len(anchors) == 10
          and sum(a["confirmed"] for a in anchors) == 8)

    # 缺候选降级：空模型 + 无底图不崩；空模型冻结 schema 仍通过
    m_empty = editor.EditorModel([], calib=None)
    check("空候选模型不崩", len(m_empty.candidates) == 0)
    import tempfile
    res_empty = editor.freeze_layout(
        m_empty, tempfile.mkdtemp(), source_meta={}, quad=None,
        clock=lambda f: "20260101_000000" if f == "%Y%m%d_%H%M%S" else "2026-01-01T00:00:00")
    check("空模型冻结 ok 且 schema 无错", res_empty["ok"] and res_empty["errors"] == [],
          res_empty.get("message", ""))

    # 字体降级：ready 取中文，False 才 ASCII，绝不并排
    check("_L ready 取中文", pages._L(True, "研究", "research") == "研究")
    check("_L not-ready 降级 ASCII", pages._L(False, "研究", "research") == "research")


# ================================================================ 显示器守卫（长期保留）
# 禁止把覆盖层画到主屏：只有雷电渲染窗口落在外接屏（x>=1920，非 DISPLAY1）
# 才允许启动可见冒烟；否则 ABORT 并以非零退出码结束。

def _display_guard():
    """返回 (allowed, detail)。枚举 LDPlayerMainFrame / RenderWindow 子窗口。"""
    try:
        import win32gui
        import win32api
        import win32con
    except Exception as e:
        return False, f"pywin32 不可用: {e}"

    mains = []

    def _enum_main(h, _):
        if win32gui.GetClassName(h) == "LDPlayerMainFrame":
            mains.append(h)
        return True

    win32gui.EnumWindows(_enum_main, None)
    if not mains:
        return False, "LDPlayerMainFrame 未找到（雷电未运行）"

    target = None
    for h in mains:
        found = []

        def _enum_child(child, _lp):
            if win32gui.GetClassName(child) == "RenderWindow":
                found.append(child)
                return False  # 停止枚举
            return True

        win32gui.EnumChildWindows(h, _enum_child, 0)
        if found:
            target = found[0]
            break

    probe = target or mains[0]
    rect = win32gui.GetWindowRect(probe)
    x0, y0, x1, y1 = rect
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    # 取显示器信息：先窗口，失败改中心点；都拿不到就 fail-closed（ABORT）
    device, work, flags = "?", "?", None
    mon = win32api.MonitorFromWindow(probe, win32con.MONITOR_DEFAULTTONULL)
    if not mon:
        mon = win32api.MonitorFromPoint((cx, cy), win32con.MONITOR_DEFAULTTONULL)
    if mon:
        info = win32api.GetMonitorInfo(mon) or {}
        device = info.get("Device", "?")
        work = info.get("Work", "?")
        flags = info.get("Flags", 0)
    MONITORINFOF_PRIMARY = 0x1
    # 部分离屏判定：窗口 rect 与所有显示器 rcMonitor 的交集面积必须 ≥ rect 面积；
    # 交集不足（含完全不可见，交集=0）→ partially-offscreen=true → ABORT。
    mon_rects = []
    try:
        for _hmon, _hdc, mrect in win32api.EnumDisplayMonitors(None, None):
            mon_rects.append(mrect)
    except Exception:
        mon_rects = []
    warea = max(0, x1 - x0) * max(0, y1 - y0)
    inter = 0
    for (mx0, my0, mx1, my1) in mon_rects:
        ix0, iy0 = max(x0, mx0), max(y0, my0)
        ix1, iy1 = min(x1, mx1), min(y1, my1)
        inter += max(0, ix1 - ix0) * max(0, iy1 - iy0)
    partially_off = bool(mon_rects) and inter < warea

    # fail-closed：
    #  1) 显示器拿不到 → ABORT；
    #  2) GetMonitorInfo Flags 带 PRIMARY(0x1) 或设备是 \\.\DISPLAY1 → 硬拒绝；
    #  3) 窗口与可见显示器交集不足（部分/完全离屏）→ ABORT；
    #  4) rect 必须完全落在右屏区 1920..3840 × 0..1080。
    reason = None
    if mon is None:
        reason = "monitor unknown"
    elif flags & MONITORINFOF_PRIMARY:
        reason = "primary display (Flags & MONITORINFOF_PRIMARY)"
    elif device in ("?", r"\\.\DISPLAY1"):
        reason = f"device={device} rejected"
    elif partially_off:
        reason = (f"partially-offscreen=true inter={inter}/{warea} "
                  f"(rect 与可见显示器交集不足)")
    elif not (x0 >= 1920 and x1 <= 3840 and y0 >= 0 and y1 <= 1080):
        reason = f"rect out of secondary zone rect=({x0},{y0})-({x1},{y1})"
    on_secondary = reason is None
    detail = (f"device={device} flags={flags} rect=({x0},{y0})-({x1},{y1}) center=({cx},{cy}) "
              f"work={work} inter={inter}/{warea} partially_off={partially_off} "
              f"main={hex(mains[0])} target={hex(probe)} reject={reason or 'none'}")
    return on_secondary, detail


# ================================================================ 可见阶段（best-effort）

def live_phase(seconds):
    log("== live phase (best-effort) ==")
    import win32gui
    import win32con
    import win32api
    allowed, detail = _display_guard()
    log(f"[GUARD] {detail}")
    if not allowed:
        log("ABORT: LDPlayer on primary display（未落在外接屏，禁止启动覆盖层）")
        log(f"ABORT reason: {detail.split('reject=', 1)[-1]}")
        log("live_executed=0（守卫拦截，未启动覆盖层，未截图）")
        raise SystemExit(2)
    log("live_executed=1（守卫放行）")

    proc = subprocess.Popen(
        [sys.executable, os.path.join(ROOT, "run_overlay.py"),
         "--show", "--mode", "PANEL", "--run-seconds", str(seconds)],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    log(f"spawned run_overlay.py pid={proc.pid}")

    hwnd = _wait_window(win32gui, timeout=15)
    if not hwnd:
        log("SKIP live: clashlab-overlay 窗口未出现（雷电未运行/可见模式未通）")
        _terminate(proc)
        return

    time.sleep(2.0)
    rect = win32gui.GetWindowRect(hwnd)
    log(f"overlay window rect={rect}")
    W = rect[2] - rect[0]
    panel_w = min(420.0, W * 0.45)
    px = rect[0] + W - panel_w

    # 逐页截图（research 默认页）
    _grab(win32gui, hwnd, os.path.join(ROOT, "out", "overlay", "ui_research.png"))
    log("saved ui_research.png")

    # 点采集标签（标签条 y≈19，第二枚按钮中心 ≈ px+147）
    _click(win32api, win32con, px + 147, rect[1] + 19)
    time.sleep(0.8)
    _grab(win32gui, hwnd, os.path.join(ROOT, "out", "overlay", "ui_collect.png"))
    log("saved ui_collect.png")

    # 点设置标签（第三枚按钮中心 ≈ px+239）
    _click(win32api, win32con, px + 239, rect[1] + 19)
    time.sleep(0.8)
    _grab(win32gui, hwnd, os.path.join(ROOT, "out", "overlay", "ui_setting.png"))
    log("saved ui_setting.png")

    # 回研究页（第一枚按钮中心 ≈ px+55），点一次候选框（画布中心）+ 冻结按钮
    _click(win32api, win32con, px + 55, rect[1] + 19)
    time.sleep(0.8)
    _click(win32api, win32con, px + panel_w / 2, rect[1] + 300)
    time.sleep(0.3)
    _drag(win32api, win32con, px + panel_w / 2, rect[1] + 300,
          px + panel_w / 2 + 30, rect[1] + 300 + 24)
    log("best-effort: 候选框点击+拖动")
    _click(win32api, win32con, px + 72, rect[1] + 588)
    log("best-effort: 点击 冻结 layout")
    time.sleep(1.0)

    proc.wait(timeout=seconds + 10)


def _wait_window(win32gui, timeout):
    t0 = time.time()
    while time.time() - t0 < timeout:
        found = []

        def cb(h, _):
            if win32gui.GetWindowText(h) == "clashlab-overlay" and win32gui.IsWindowVisible(h):
                found.append(h)
            return True

        win32gui.EnumWindows(cb, None)
        if found:
            return found[0]
        time.sleep(0.5)
    return None


def _click(win32api, win32con, x, y):
    win32api.SetCursorPos((int(x), int(y)))
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


def _drag(win32api, win32con, x0, y0, x1, y1):
    win32api.SetCursorPos((int(x0), int(y0)))
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    for i in range(1, 11):
        win32api.SetCursorPos((int(x0 + (x1 - x0) * i / 10), int(y0 + (y1 - y0) * i / 10)))
        time.sleep(0.02)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


def _grab(win32gui, hwnd, path):
    try:
        from PIL import ImageGrab
        rect = win32gui.GetWindowRect(hwnd)
        img = ImageGrab.grab(bbox=rect)
        img.save(path)
    except Exception as e:
        log(f"screenshot fail {path}: {e}")


def _terminate(proc):
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except Exception:
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--seconds", type=float, default=25.0)
    a = ap.parse_args()

    ok = True
    try:
        static_phase()
    except Exception:
        ok = False
        log("static exception:\n" + traceback.format_exc())
    if a.live:
        try:
            live_phase(a.seconds)
        except SystemExit as e:
            os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
            with open(LOG_PATH, "w", encoding="utf-8") as f:
                f.write("\n".join(LINES) + "\n")
            sys.exit(e.code or 2)
        except Exception:
            log("live exception:\n" + traceback.format_exc())

    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(LINES) + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
