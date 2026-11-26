# -*- coding: utf-8 -*-
"""覆盖层运行时主循环：单进程单窗口，HUD/PANEL 双模式，F8/ESC 同帧切换。

路线：imgui_bundle(1.93) + GLFW/OpenGL3 + Win32 扩展样式控制透明穿透。
严禁注入/ hook/ 读内存；只靠自身窗口 + 屏幕坐标。
"""
from __future__ import annotations

import csv
import ctypes
import json
import os
import sys
import time
from types import SimpleNamespace

import win32con
import win32gui

from . import draw as hud_draw
from . import keys as keybind
from . import perf as _perf
from . import tactics
from .config import load_overlay_config, save_overlay_config
from .state import DEFAULT_QUAD, load_state, reload

# 引擎模式重要防御标注的读取缓存（1.5s 一次，不每帧读盘）
_TACT = {"doc": None, "t": 0.0}

# v5：plan.json 标注缓存（mtime 侦测 + 1.5s ttl），LLM 引擎画 marks 用
_PLAN_CACHE = {"doc": None, "t": 0.0, "mtime": 0.0}


def _plan_doc(rt, ttl=1.5):
    # 优化3：ttl 未到直接返回缓存，不再每帧 os.stat（stat 是系统调用，60fps 白跑）；
    # 仅 ttl 到期才 stat 比对 mtime，mtime 未变也不重载，只刷新 ttl。
    path = os.path.join(rt.root, "out", "overlay", "tactics", "plan.json")
    now = time.time()
    if _PLAN_CACHE["doc"] is not None and now - _PLAN_CACHE["t"] <= ttl:
        return _PLAN_CACHE["doc"]
    try:
        mt = os.stat(path).st_mtime
    except OSError:
        mt = 0.0
    if _PLAN_CACHE["doc"] is None or mt != _PLAN_CACHE["mtime"]:
        _PLAN_CACHE["doc"] = tactics.load_plan(rt.root)
        _PLAN_CACHE["mtime"] = mt
    _PLAN_CACHE["t"] = now
    return _PLAN_CACHE["doc"]


def _tactics_rows(rt, ttl=1.5):
    now = time.time()
    if _TACT["doc"] is None or now - _TACT["t"] > ttl:
        _TACT["doc"] = tactics.load_local(rt.state.root)
        _TACT["t"] = now
    return _TACT["doc"].get("rows") or []

user32 = ctypes.windll.user32

WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOOLWINDOW = 0x00000080

GA_ROOT = 2
SW_HIDE = 0
SW_SHOWNOACTIVATE = 4

# ---- 主屏禁区守卫（默认开启，硬底线）：渲染窗口落在主显示器时强制隐藏 ----
GUARD_PRIMARY_DISPLAY = True
MONITOR_DEFAULTTONULL = 0
MONITORINFOF_PRIMARY = 0x00000001


class MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint),
                ("rcMonitor", ctypes.c_long * 4),
                ("rcWork", ctypes.c_long * 4),
                ("dwFlags", ctypes.c_uint)]


def _render_monitor(child):
    """MonitorFromWindow + GetMonitorInfo：返回 (hmon, primary_bool, rcMonitor)。
    失败返回 (None, False, None)。用 MONITORINFOF_PRIMARY 标志判定，不靠坐标。"""
    if not child:
        return None, False, None
    hmon = user32.MonitorFromWindow(child, MONITOR_DEFAULTTONULL)
    if not hmon:
        return None, False, None
    mi = MONITORINFO()
    mi.cbSize = ctypes.sizeof(mi)
    if not user32.GetMonitorInfoW(hmon, ctypes.byref(mi)):
        return hmon, False, None
    return hmon, bool(mi.dwFlags & MONITORINFOF_PRIMARY), tuple(mi.rcMonitor)


# ---- 优化1：渲染目标句柄缓存（IsWindow 失效才全量重枚举，去掉每 30 帧盲枚举）----
_TARGET_CACHE = {"main": None, "child": None, "none_t": 0.0}


def get_render_target(force=False):
    """返回 (main, child)。缓存有效（child 句柄仍在）直接复用；仅 IsWindow 失效
    或 force 时才 find_render_target() 全量枚举。目标缺失时给 2s 冷却，避免游戏
    未开时每帧 EnumWindows+EnumChildWindows。"""
    main, child = _TARGET_CACHE["main"], _TARGET_CACHE["child"]
    alive = bool(child) and bool(win32gui.IsWindow(child))
    now = time.perf_counter()
    if force or not alive:
        if child or now - _TARGET_CACHE["none_t"] >= 2.0:
            main, child = find_render_target()
            _TARGET_CACHE["main"], _TARGET_CACHE["child"] = main, child
            if child is None:
                _TARGET_CACHE["none_t"] = now
    return _TARGET_CACHE["main"], _TARGET_CACHE["child"]


# ---- 优化2：_render_monitor 结果缓存 1/30 帧（同句柄不重复 MonitorFromWindow/GetMonitorInfo）----
_MON_CACHE = {"child": None, "hmon": None, "primary": False, "rc": None, "n": 0}


def get_render_monitor(child, frame_n):
    """同 child 句柄时每 30 帧刷新一次 monitor 结果，中间帧直接返回缓存。"""
    if (child is not None and child == _MON_CACHE["child"]
            and _MON_CACHE["hmon"] is not None and frame_n % 30 != 1):
        return _MON_CACHE["hmon"], _MON_CACHE["primary"], _MON_CACHE["rc"]
    hmon, on_primary, rc = _render_monitor(child)
    _MON_CACHE.update(child=child, hmon=hmon, primary=on_primary, rc=rc)
    return hmon, on_primary, rc


def _display_topology():
    """EnumDisplayMonitors 全量快照：[(hmon_hex, rcMonitor, primary_bool)]。"""
    out = []

    def _cb(hmon, _hdc, _rc, _data):
        mi = MONITORINFO()
        mi.cbSize = ctypes.sizeof(mi)
        if user32.GetMonitorInfoW(hmon, ctypes.byref(mi)):
            out.append((hex(hmon), tuple(mi.rcMonitor),
                        bool(mi.dwFlags & MONITORINFOF_PRIMARY)))
        return 1

    cb = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_voidp, ctypes.c_voidp,
                            ctypes.POINTER(ctypes.c_long * 4), ctypes.c_voidp)
    user32.EnumDisplayMonitors(None, None, cb(_cb), 0)
    return out


def _rect_intersection_area(rect, monitors):
    """rect=(l,t,r,b) 与所有 monitor rc 的并集求交，返回交集面积。"""
    al, at, ar, ab = rect
    total = 0
    for _, (ml, mt, mr, mb), _ in monitors:
        il, it = max(al, ml), max(at, mt)
        ir, ib = min(ar, mr), min(ab, mb)
        if ir > il and ib > it:
            total += (ir - il) * (ib - it)
    return total


def _fg_belongs_to_ld(root, main_h):
    """前台根窗口是否属于雷电（主窗本身或其后代）。只读判定，不切前台。"""
    if not root or not main_h:
        return False
    if root == main_h:
        return True
    try:
        return bool(win32gui.IsChild(main_h, root))
    except Exception:
        return False


def _last_input_idle_s():
    """GetLastInputInfo：用户空闲秒数（只读，不打断）。"""
    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]
    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
    if not user32.GetLastInputInfo(ctypes.byref(lii)):
        return -1.0
    return (user32.GetTickCount() - lii.dwTime) / 1000.0


# ---------------------------------------------------------------- 目标窗口探测
def find_render_target():
    """找 LDPlayerMainFrame；取其可见后代客户区最大者为渲染面。返回 (main, child)。"""
    cands = []

    def _cb(h, _):
        if win32gui.GetClassName(h) == "LDPlayerMainFrame" and win32gui.IsWindowVisible(h):
            cands.append((h, win32gui.GetWindowText(h) or ""))

    win32gui.EnumWindows(_cb, None)
    if not cands:
        return None, None
    # 多开时选对实例：标题恰为「雷电模拟器」优先（CoC），其次不带 -1/-2 后缀
    def _key(item):
        _h, title = item
        s = title.strip()
        if s == "雷电模拟器":
            return (0, len(s), _h)
        if "雷电" in s and not s.endswith(("-1", "-2", "-3", "-4")):
            return (1, len(s), _h)
        return (2, len(s), _h)
    cands.sort(key=_key)
    main = [cands[0][0]]
    best = [None, 0]

    def _walk(h):
        kids = []
        win32gui.EnumChildWindows(h, lambda k, _: kids.append(k), None)
        for k in kids:
            if win32gui.IsWindowVisible(k):
                r = win32gui.GetClientRect(k)
                area = r[2] * r[3]
                if area > best[1]:
                    best[0], best[1] = k, area
                _walk(k)

    _walk(main[0])
    return main[0], best[0]


def target_rect(child):
    pt = win32gui.ClientToScreen(child, (0, 0))
    r = win32gui.GetClientRect(child)
    return pt[0], pt[1], r[2], r[3]


def _grab_window_frame(hwnd):
    """PrintWindow(PW_RENDERFULLCONTENT) 尽力抓窗口为 BGR ndarray；失败返回 None。
    P1-6 专用抓帧通路；不改 vision/geo/snap/template_match 任何内部实现。"""
    try:
        import numpy as np
        import win32ui
        l, t, r, b = win32gui.GetWindowRect(hwnd)
        w, h = r - l, b - t
        if w <= 0 or h <= 0:
            return None
        hwnd_dc = win32gui.GetWindowDC(hwnd)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()
        bmp = win32ui.CreateBitmap()
        bmp.CreateCompatibleBitmap(mfc_dc, w, h)
        save_dc.SelectObject(bmp)
        PW_RENDERFULLCONTENT = 0x00000002
        ctypes.windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), PW_RENDERFULLCONTENT)
        info = bmp.GetInfo()
        bits = bmp.GetBitmapBits(True)
        arr = np.frombuffer(bits, dtype=np.uint8).reshape(
            info["bmHeight"], info["bmWidth"], 4)
        frame = arr[:, :, :3].copy()  # BGRA -> BGR（vision.detect_boundary 口径）
        win32gui.DeleteObject(bmp.GetHandle())
        save_dc.DeleteDC()
        mfc_dc.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwnd_dc)
        return frame
    except Exception:
        return None


# PANEL 窗口外置几何（任务1，授权段）：窗口即面板，panel_w=440，不套比例公式
PANEL_PW = 440.0
PANEL_GAP = 8.0
# P2-5：面板内容最小可用高度。实测 H=259（本机 1080p、客户区底 813、任务栏顶 1032）
# 时底部三行状态（聚焦/高亮/来源）与列表互压、行被裁（_p2b/panel_baseline_down_window.png）；
# 顶部固定栈 STACK_TOP=112 + 底部三行约 66 + 至少 4 行列表约 104 + 余量 -> 360。
PANEL_MIN_H = 360.0
SPI_GETWORKAREA = 0x0030


class _RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


def _primary_workarea_bottom(sh: int) -> int:
    """主显示器工作区底（避开任务栏）；取不到时退回屏幕高。物理像素（进程已 DPI 感知）。"""
    try:
        rc = _RECT()
        if user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, ctypes.byref(rc), 0):
            if rc.bottom > 0:
                return int(rc.bottom)
    except Exception:
        pass
    return int(sh)


def _panel_zone_fit(zone, tx, ty, tw, th, sw, sh, work_bottom):
    """算某一档落点；放不下返回 None（绝不返回越界窗口）。
    right : 客户区右侧外，宽 PANEL_PW、高=客户区高（纵向夹进屏幕）；
    down  : 客户区下方，宽 PANEL_PW，水平**居中于客户区**后夹进屏幕，
            高 = 工作区底 - y（不盖任务栏），< PANEL_MIN_H 判不可用；
    inner : 客户区右侧 PANEL_PW 宽条带（窗口即面板）；不再覆盖整个客户区——
            旧实现返回整客户区 1280x720，左侧被不透明底板盖住且拦截鼠标（P2-5b）。
            最后兜底，总是可用（条带夹进主屏）。"""
    if zone == "right":
        # 面板内容需要约 700px 高；目标客户区常常只有 ~560（1280x720 缩放），
        # 之前直接取 th 导致设置页底部被裁。这里取 max(th, 700) 并夹进工作区。
        h = float(min(max(float(th), 700.0), float(work_bottom - ty), float(sh)))
        y = float(max(0, min(ty, sh - int(h))))
        x = float(tx + tw + PANEL_GAP)
        if h < PANEL_MIN_H or x < 0 or x + PANEL_PW > sw:
            return None
        return (x, y, PANEL_PW, h)
    if zone == "down":
        y = float(ty + th + PANEL_GAP)
        h = float(work_bottom - y)
        if h < PANEL_MIN_H:
            return None
        x = float(tx + (tw - PANEL_PW) / 2.0)   # 旧实现 x=tx+tw+gap：客户区靠右时整窗出屏
        x = max(0.0, min(x, sw - PANEL_PW))
        return (x, y, PANEL_PW, h)
    # inner：窗口=客户区右侧条带（宽 PANEL_PW / 高 th），贴客户区右缘后夹进主屏。
    # 条带即窗口，不存在“窗口内透明区”，游戏其余区域不属于覆盖层 -> 鼠标直接落到游戏。
    w = float(min(PANEL_PW, max(float(tw), 1.0)))
    h = float(min(float(th), float(sh)))
    y = float(max(0.0, min(float(ty), float(sh) - h)))
    x = float(max(0.0, min(float(tx + tw) - w, float(sw) - w)))
    return (x, y, w, h)


def _panel_place(tx, ty, tw, th, pref):
    """PANEL 模式窗口放置（P2-5 实测修订；P2-5b 修 inner）：right=客户区右侧外；
    down=客户区下方（工作区剩余高度，< PANEL_MIN_H 判不可用）；
    inner=客户区右侧 PANEL_PW 宽条带（叠游戏内右侧，不再覆盖整个客户区）。
    pref ∈ {right,down,inner,auto}；auto(v9-④) 按 右→下→内 选第一个放得下的；
    显式档位放不下时同样降级（调用方记一次 WARN，不再每帧刷日志）。
    返回 (x, y, w, h, zone)，任何外置档都保证整体落在主屏内。"""
    sw = int(user32.GetSystemMetrics(0))
    sh = int(user32.GetSystemMetrics(1))
    work_bottom = _primary_workarea_bottom(sh)
    if pref == "inner":
        order = ("inner",)
    elif pref == "down":
        order = ("down", "right", "inner")
    elif pref == "right":
        order = ("right", "down", "inner")
    else:  # auto / "" / default / 未知值
        order = ("right", "down", "inner")
    for zone in order:
        fit = _panel_zone_fit(zone, tx, ty, tw, th, sw, sh, work_bottom)
        if fit is not None:
            return (fit[0], fit[1], fit[2], fit[3], zone)
    # 理论不可达（inner 恒可用）；保险起见按 inner 条带返回
    fit = _panel_zone_fit("inner", tx, ty, tw, th, sw, sh, work_bottom)
    return (fit[0], fit[1], fit[2], fit[3], "inner")

# ---------------------------------------------------------------- ctx 实现
class _Ctx:
    """暴露给 pages.draw_panel 的运行时上下文。"""

    def __init__(self, rt):
        self.rt = rt
        self.textures: dict[str, int] = {}

    @property
    def font_ready(self) -> bool:
        """CJK 字体是否真的加载成功（由 _load_cjk_font 写 rt.font_ready）。

        pages._font_ready 优先读这个标志；缺了它就只能回落到 config 里的静态
        值 False，导致中文可用却全局画英文，中英标签叠在一起。
        """
        return bool(getattr(self.rt, "font_ready", False))

    # 模式/页/live 状态写回
    def set_mode(self, mode: str) -> None:
        self.rt.request_mode(mode)

    def set_page(self, page: str) -> None:
        self.rt.state.page = page

    def set_live(self, live: bool) -> None:
        self.rt.state.live = bool(live)
        self.rt.log(f"set_live -> {bool(live)}")

    # 冻结 layout：委托 editor.freeze_layout，原样返回结果 dict
    def freeze_layout(self, model, source_meta=None, quad=None, grid=44):
        try:
            from . import editor
        except Exception as e:
            return {"ok": False, "message": f"editor import fail: {e}", "errors": [str(e)]}
        if isinstance(model, dict):
            model = SimpleNamespace(candidates=model.get("candidates", []))
        layouts_dir = os.path.join(self.rt.root, "layouts")
        return editor.freeze_layout(
            model, layouts_dir, source_meta=source_meta,
            quad=quad or self.rt.state.quad_px, grid=grid)

    @property
    def geo(self):
        return self.rt.calib

    @property
    def touch(self):
        try:
            from clashlab import touch  # 触控线独占；可能不存在
            return touch
        except Exception:
            return None

    def reload(self) -> None:
        self.rt.request_reload()

    def log(self, msg: str) -> None:
        self.rt.log(str(msg))

    # 面板线追加接口（见 a_answers.md）
    def panel_rect(self):
        return self.rt.panel_rect()

    def dpi_scale(self) -> float:
        return self.rt.dpi_scale()

    def mouse(self):
        return self.rt.mouse_pos()

    def texture(self, path_or_ndarray, key=None, max_px=None) -> int:
        return self.rt.texture_register(path_or_ndarray, key=key, max_px=max_px)

    def texture_invalidate(self, key: str) -> None:
        self.textures.pop(key, None)

    def request_farm_start(self) -> None:
        self.rt.farm_request = "start"
        self.rt.log("farm request: start")

    def request_farm_stop(self) -> None:
        self.rt.farm_request = "stop"
        self.rt.log("farm request: stop")

    def request_study(self, opts=None) -> None:
        self.rt.study_request = dict(opts or {})
        self.rt.log(f"study request: {self.rt.study_request}")

    def request_data_prep(self) -> None:
        """v9-⑥闭环：面板「自动采集」按钮 -> 置位 data_prep_request，主循环下一帧消费
        （表优先，无表抓帧+detect；自动≤2次/启动）。"""
        self.rt.data_prep_request = True
        self.rt.log("data-prep request set (auto capture button)")

    def request_exit(self) -> None:
        """P0-2：面板「退出」按钮 -> 主循环下一帧 break，走 destroy_window/terminate 干净退出。"""
        self.rt.exit_request = True
        self.rt.log("panel: exit requested")

    def request_recalib(self) -> None:
        """P1-6：面板「重新对位」按钮 -> 抓帧 + vision.detect_boundary 重算标定。"""
        self.rt.request_recalib()

    @property
    def recalib_msg(self):
        return getattr(self.rt, "recalib_msg", ("neutral", ""))

    @property
    def view_warn(self) -> bool:
        return bool(getattr(self.rt.state, "view_warn", False))

    def set_view_warn(self, on: bool) -> None:
        self.rt.state.view_warn = bool(on)
        self.rt.log(f"view_warn badge -> {bool(on)}")

    def request_focus(self) -> None:
        self.rt.take_focus(True)

    def release_focus(self) -> None:
        self.rt.take_focus(False)


# ---------------------------------------------------------------- 运行时主体
class _Runtime:
    def __init__(self, root: str, cfg: dict):
        self.root = os.path.abspath(root)
        self.cfg = cfg
        self.state = load_state(self.root)
        self.state.mode = "HUD"
        self.log_path = os.path.join(self.root, "out", "overlay", "overlay.log")
        self.reload_request = False
        self.farm_request = None
        self.study_request = None
        self.data_prep_request = None  # v9-⑥：info.json 缺失/过期的待抓帧标记（离线置位）
        self._data_prep_attempts = 0  # v9-⑥闭环：一次启动自动尝试上限 2 次（内存计数）
        self.data_prep_msg = ("neutral", "")  # v9-⑥闭环：失败 HUD 提示（color, text）
        self.exit_request = False  # P0-2：面板「退出」按钮置位，主循环下一帧退出
        self.calib = None
        self._build_calib()
        self._prev_keys: dict = {}
        self._frame_times = []

    # -- 日志 --
    def log(self, msg: str) -> None:
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        # 窗口标题可能带零宽字符（LDPlayer 标题含 ZWSP），GBK 控制台 print 会抛 UnicodeEncodeError
        safe = line.replace("\u200b", "").replace("\ufeff", "")
        try:
            print(safe)
        except UnicodeEncodeError:
            enc = getattr(sys.stdout, "encoding", None) or "utf-8"
            print(safe.encode(enc, "replace").decode(enc, "replace"))
        try:
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass

    # v9-②：当前标定视口（客户区 px）；None = 未按视口构造（退回旧绝对 quad）
    _calib_vp = (1280.0, 720.0)

    def _build_calib(self, tw: float = 1280.0, th: float = 720.0):
        """v9-② 视口适配：quad_norm(0–1) 按当前 (tw, th) 还原像素再求单应；
        归一化缺失/非法时退回旧绝对 quad_px（旧行为不崩）。换算语义仍走 geo.Calib。
        """
        try:
            from clashlab.geo import Calib
            qn = getattr(self.state, "quad_norm", None)
            if qn and len(qn) == 4 and tw > 1.0 and th > 1.0:
                self.calib = Calib.from_quad_norm(qn, tw, th)
                self._calib_vp = (float(tw), float(th))
            else:
                self.calib = Calib.from_quad(self.state.quad_px)
                self._calib_vp = (1280.0, 720.0)
        except Exception as e:
            self.calib = None
            self.log(f"calib build fail: {e}")

    # ---- v9-⑥：config/view_quads.json 查表优先（detect_boundary 仅在无表时用）----
    def _load_view_quads_norm(self):
        """读 config/view_quads.json；仅接受验收通过(inside/PASS)的 quad。
        返回归一化四点(T,R,B,L)或 None。离线只走查表，不抓帧。"""
        path = os.path.join(self.root, "config", "view_quads.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                doc = json.load(f)
        except Exception as e:
            self.log(f"view_quads 读取跳过: {e}")
            return None
        quad = (doc or {}).get("quad") or {}
        inside = bool(quad.get("inside"))
        hw = (quad.get("HW_check") or {})
        accepted = inside and (doc.get("status") != "FAIL") and (
            not hw or hw.get("PASS") is not False)
        # L0_snapped 是另一套已验收快照（38/38 锚点），同样可查表
        snap = doc.get("L0_snapped") or {}
        sq = snap.get("quad") if isinstance(snap, dict) else None
        canvas = doc.get("canvas") or [1, 1]
        if accepted and all(k in quad for k in ("T", "R", "B", "L")):
            pts = [quad["T"], quad["R"], quad["B"], quad["L"]]
            cw, ch = float(canvas[0] or 1), float(canvas[1] or 1)
            return [[float(p[0]) / cw, float(p[1]) / ch] for p in pts]
        if sq and all(k in sq for k in ("T", "R", "B", "L")):
            pts = [sq["T"], sq["R"], sq["B"], sq["L"]]
            cw, ch = float(canvas[0] or 1), float(canvas[1] or 1)
            return [[float(p[0]) / cw, float(p[1]) / ch] for p in pts]
        return None

    def _maybe_autograb(self):
        """v9-⑥：info.json 缺失/过期的启动自动抓帧分析——只做代码路径与置位；
        真抓 PrintWindow 留实机阶段（离线不碰游戏窗口）。"""
        pj = os.path.join(self.root, "out", "prebattle", "info.json")
        try:
            missing = not os.path.exists(pj)
            stale = False
            if not missing:
                age = time.time() - os.stat(pj).st_mtime
                stale = age > 12 * 3600  # 12h 视为过期
            if missing or stale:
                self.data_prep_request = True
                self.log(f"data-prep: info.json {'缺失' if missing else '过期>12h'}"
                          f" -> 待实机自动抓帧分析（离线仅置位）")
        except Exception as e:
            self.log(f"data-prep check skip: {e}")

    # ---- v9-⑥闭环：data_prep_request 消费者（表优先，无表抓帧+detect；自动≤2次/启动）----
    DATA_PREP_MAX_ATTEMPTS = 2

    def _default_grab(self):
        """PrintWindow(PW_RENDERFULLCONTENT) 只读抓帧；不 SetForegroundWindow、不抢激活。
        离线测试可经 grab_fn 注入替换。"""
        try:
            _main, child = find_render_target()
            if not child:
                return None
            return _grab_window_frame(child)
        except Exception:
            return None

    def _default_detect(self, frame, grid_n=44):
        from clashlab import vision
        return vision.detect_boundary(frame, grid_n=grid_n)

    def _data_prep_fail(self, why: str) -> None:
        """失败统一收口：HUD 琥珀提示 + 一行日志；flag 已清，不重试刷屏。"""
        self.data_prep_msg = ("yellow", "自动采集失败，按 Insert 手动点")
        self.log(f"data-prep: {why}（第 {self._data_prep_attempts}/2 次，未重试刷屏）")

    def _write_prep_info(self, source: str, qn=None, meta=None) -> None:
        """成功落 out/prebattle/info.json：合并旧情报键，只追加 prep 元数据；原子写。"""
        pj = os.path.join(self.root, "out", "prebattle", "info.json")
        doc = {}
        try:
            with open(pj, "r", encoding="utf-8") as f:
                doc = json.load(f) or {}
        except Exception:
            doc = {}
        if not isinstance(doc, dict):
            doc = {}
        doc["prep"] = {
            "source": source,
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "quad_norm": qn,
            "meta": ({k: meta.get(k) for k in ("source", "confidence")}
                     if isinstance(meta, dict) else None),
        }
        os.makedirs(os.path.dirname(pj), exist_ok=True)
        tmp = pj + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
        os.replace(tmp, pj)

    def _consume_data_prep(self, grab_fn=None, detect_fn=None) -> None:
        """data_prep_request 消费者：一次启动自动尝试≤2次。
        1) 先查 config/view_quads.json：验收/快照表命中 -> 直接采用，不抓帧不 detect；
        2) 无表才 PrintWindow 抓帧 -> vision.detect_boundary（conf<0.4 不采用）；
        3) 成功：落 info.json、清 flag、清 HUD 提示；失败：清 flag + 一行日志 +
           HUD「自动采集失败，按 Insert 手动点」，不重试刷屏；满 2 次后只留手动按钮。
        grab_fn/detect_fn 仅供离线测试注入。"""
        if not self.data_prep_request:
            return
        if self._data_prep_attempts >= self.DATA_PREP_MAX_ATTEMPTS:
            self.data_prep_request = None
            self.log("data-prep: 自动尝试已达 2 次上限，不再自动试（面板手动采集）")
            return
        self.data_prep_request = None  # 先清 flag，防同帧重复消费
        self._data_prep_attempts += 1
        # 1) 查表优先
        try:
            qn = self._load_view_quads_norm()
            if qn:
                tw, th = self._calib_vp
                self.state.quad_norm = qn
                self.state.quad_px = [[p[0] * tw, p[1] * th] for p in qn]
                self._build_calib(tw, th)
                self._write_prep_info("view_quads_table", qn=qn)
                self.data_prep_msg = ("neutral", "")
                self.log("data-prep: view_quads 表命中，已采用（未抓帧未 detect）")
                return
        except Exception as e:
            self.log(f"data-prep table skip: {e}")
        # 2) 无表 -> 抓帧 + detect
        try:
            grab = grab_fn or self._default_grab
            frame = grab()
            if frame is None:
                self._data_prep_fail("抓帧失败（PrintWindow 不可用或未找到雷电窗口）")
                return
            detect = detect_fn or self._default_detect
            calib, meta = detect(frame, grid_n=44)
            if calib is None:
                self._data_prep_fail("detect_boundary 未识别到地图轮廓")
                return
            conf = float((meta or {}).get("confidence", 0) or 0)
            if conf < 0.4:
                self._data_prep_fail(f"detect 置信 {conf:.3f}<0.4 未采用")
                return
            self.calib = calib
            vw, vh = self._calib_vp
            self.state.quad_px = [[float(x), float(y)] for x, y in meta["quad"]]
            self.state.quad_norm = [[float(x) / vw, float(y) / vh]
                                    for x, y in meta["quad"]]
            self._write_prep_info("detect_boundary", qn=self.state.quad_norm, meta=meta)
            self.data_prep_msg = ("neutral", "")
            self.log(f"data-prep: detect 成功 conf={conf:.3f}，info.json 已落盘")
        except Exception as e:
            self._data_prep_fail(f"异常 {e!r}")

    # ---- P1-6 一键重对位：只接线 vision.detect_boundary/safe_calib，不改其内部 ----
    recalib_msg: tuple = ("neutral", "")

    def request_recalib(self):
        """v9-⑥ 查表优先：config/view_quads.json 有验收 quad -> 直接采用，不抓帧不检测；
        无表才抓帧 -> vision.detect_boundary -> 重算 Calib；失败保留旧标定并报中文。"""
        try:
            qn = self._load_view_quads_norm()
            if qn:
                self.state.quad_norm = qn
                tw, th = self._calib_vp
                self.state.quad_px = [[p[0] * tw, p[1] * th] for p in qn]
                self._build_calib(tw, th)
                self.recalib_msg = ("green", "已采用 view_quads.json 验收标定")
                self.log("recalib: view_quads table adopted (no grab)")
                return
        except Exception as e:
            self.log(f"recalib table skip: {e}")
        try:
            _main, child = find_render_target()
            if not child:
                self.recalib_msg = ("yellow", "未找到雷电窗口，无法重对位")
                self.log("recalib: no render target")
                return
            frame = _grab_window_frame(child)
            if frame is None:
                self.recalib_msg = ("yellow", "抓帧失败（PrintWindow 不可用），未改动标定")
                self.log("recalib: grab frame failed")
                return
            from clashlab import vision
            calib, meta = vision.detect_boundary(frame, grid_n=44)
            if calib is None:
                self.recalib_msg = ("yellow", "未识别到地图轮廓，标定未改动；请手动核对")
                self.log(f"recalib: no boundary meta={meta}")
                return
            # v6-B4 置信分档：conf<0.4 不许报成功也不采用（琥珀：置信偏低建议再点一次）；
            # 0.4–0.6 中间档（琥珀：完成但置信中等，建议核对）；≥0.6 才报成功（绿）。
            conf = float(meta.get("confidence", 0) or 0)
            if conf < 0.4:
                self.recalib_msg = ("yellow",
                                    f"识别置信偏低（{conf:.2f}），建议再点一次；标定未采用")
                self.log(f"recalib LOW conf={conf:.3f} rejected; old calib kept")
            else:
                from clashlab.geo import Calib
                self.calib = calib
                self.state.quad_px = [[float(x), float(y)] for x, y in meta["quad"]]
                # v9-②：检测到的像素 quad 按当前视口反推归一化，供后续尺寸跟随
                vw, vh = self._calib_vp
                self.state.quad_norm = [[float(x) / vw, float(y) / vh]
                                        for x, y in meta["quad"]]
                if conf < 0.6:
                    self.recalib_msg = ("yellow",
                                        f"重对位完成（置信 {conf:.2f}，中等），建议核对画面")
                    self.log(f"recalib MID conf={conf:.3f} accepted; verify on screen")
                else:
                    self.recalib_msg = ("green",
                                        f"重对位成功 source={meta.get('source')} "
                                        f"conf={conf:.2f}")
                    self.log(f"recalib OK source={meta.get('source')} "
                             f"conf={conf:.3f} quad={meta.get('quad')}")
        except Exception as e:
            self.recalib_msg = ("yellow", f"重对位异常：{e}")
            self.log(f"recalib error: {e!r}")

    def request_mode(self, mode: str) -> None:
        self.state.mode = mode

    def request_reload(self) -> None:
        self.reload_request = True

    def panel_rect(self):
        # 面板本地物理像素可用区（右侧栏内缩 12px，预留 34px 标签条）
        x, y, w, h = 0.0, 34.0, 0.0, 0.0
        # 实际由主循环按窗口尺寸填回
        return (12.0, 42.0, max(0.0, self._win_w - 24.0), max(0.0, self._win_h - 54.0))

    def dpi_scale(self) -> float:
        try:
            dpi = user32.GetDpiForWindow(self._hwnd)
            return (dpi or 96) / 96.0
        except Exception:
            return 1.0

    def mouse_pos(self):
        from imgui_bundle import imgui
        io = imgui.get_io()
        return (io.mouse_pos.x, io.mouse_pos.y,
                bool(io.mouse_down[0]), bool(io.mouse_down[1]),
                io.mouse_wheel)

    def texture_register(self, path_or_ndarray, key=None, max_px=None) -> int:
        # 纹理上传由可见后端扩展；骨架阶段返回 0 占位，第二阶段实现 mtime 缓存
        return 0

    def take_focus(self, on: bool) -> None:
        # 不抢前台：SetForegroundWindow 会把雷电挤到后台（设计文档 §2 备注 / 父指令硬约束）。
        # PANEL 可点击性由帧级自喂鼠标兜底，此 facade 保持空实现，不做任何前台切换。
        return

    # -- 主循环由 run() 驱动 --
    _win_w = 1.0
    _win_h = 1.0
    _hwnd = None


def run(root: str, config: dict | None = None) -> None:
    cfg = load_overlay_config(root)
    if isinstance(config, dict):
        cfg.update(config)
    rt = _Runtime(root, cfg)
    rt.log("overlay runtime start")
    # v9-⑥：启动即查 info.json 缺失/过期（离线仅置位，真抓帧留实机）
    rt._maybe_autograb()

    show = bool(cfg.get("show", False))
    self_check_seconds = float(cfg.get("self_check_seconds", 30))

    # 不可见自检：不创建 GL 窗口，只做数据/几何自检后退出
    if not show:
        _self_check(rt, self_check_seconds)
        return

    # ---- 主屏禁区守卫：启动即检测；雷电在主显示器则不进可见循环 ----
    allow_primary = bool(cfg.get("allow_primary", False))
    main_h, child = find_render_target()
    monitors = _display_topology()
    # 单屏自适应放行：仅 1 块显示器时主屏守卫自动失效（等价 allow_primary），
    # 打 WARN；≥2 块显示器仍按原守卫拦主屏（多屏才是守卫本意）；显式 --allow-primary 保留。
    if len(monitors) < 2 and not allow_primary:
        allow_primary = True
        warn = ("[WARN] single monitor: primary guard auto-relaxed (only 1 display present)")
        rt.log(warn)
        print(warn)
    elif allow_primary:
        warn = ("[WARN] --allow-primary ACTIVE: overlay may render on the PRIMARY display "
                "and cover the user's workspace; this escape hatch is for one-off validation "
                "only, not recommended for daily use.")
        rt.log(warn)
        print(warn)
    # 目标矩形：优先渲染子窗口 GetWindowRect，回退主框
    if child:
        tgt_rect = win32gui.GetWindowRect(child)
    elif main_h:
        tgt_rect = win32gui.GetWindowRect(main_h)
    else:
        tgt_rect = None
    _m, _p, _rc = _render_monitor(child)

    # 显示器拓扑快照（每次启动写盘，单/双屏一眼可辨）
    topo = {
        "ts": time.strftime("%H:%M:%S"),
        "monitors": [{"hmon": h, "rc": list(r), "primary": p} for h, r, p in monitors],
        "monitor_count": len(monitors),
        "target_hwnd": hex(child) if child else (hex(main_h) if main_h else None),
        "target_rect": list(tgt_rect) if tgt_rect else None,
        "target_monitor": {"hmon": hex(_m) if _m else None,
                           "primary": _p, "rcMonitor": list(_rc) if _rc else None},
    }
    # 完全落在可视桌面并集判定
    if tgt_rect:
        area = (tgt_rect[2] - tgt_rect[0]) * (tgt_rect[3] - tgt_rect[1])
        inter = _rect_intersection_area(tgt_rect, monitors)
        topo["target_area"] = area
        topo["visible_intersection_area"] = inter
        topo["partially_offscreen"] = inter < area
    else:
        topo["partially_offscreen"] = None
    try:
        with open(os.path.join(root, "out", "overlay", "display_topology.json"),
                   "w", encoding="utf-8") as f:
            json.dump(topo, f, ensure_ascii=False, indent=2)
    except Exception as e:
        rt.log(f"display_topology write fail: {e}")

    if topo.get("partially_offscreen"):
        rt.log(f"[GUARD] partially-offscreen=true target_rect={tgt_rect} "
               f"visible_intersection={topo.get('visible_intersection_area')} "
               f"< target_area={topo.get('target_area')}")

    # 单显示器环境一律拒绝可见（防止盖住用户工作区）；主屏命中同样拒绝
    block = GUARD_PRIMARY_DISPLAY and not allow_primary and (_p or len(monitors) < 2)
    if block:
        vis = ",".join(f"{r}" for _, r, _ in monitors)
        why = ("target on primary display" if _p else "only primary monitor available")
        msg = (f"[GUARD] {why}; monitors={len(monitors)} "
               f"({'no secondary' if len(monitors) < 2 else 'secondary present'}). "
               f"target_rect={tgt_rect} visible desktop={vis}. "
               f"ACTION: connect secondary display, or move LDPlayer inside visible desktop, "
               f"or pass --allow-primary (not recommended).")
        rt.log(msg)
        print(msg)
        return

    # ---- 可见模式：GLFW + ImGui ----
    import glfw
        # noqa: E401
    from imgui_bundle import imgui
    from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

    user32.SetProcessDpiAwarenessContext(-4)
    glfw.init()
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 2)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.DECORATED, False)
    glfw.window_hint(glfw.TRANSPARENT_FRAMEBUFFER, True)
    glfw.window_hint(glfw.FOCUSED, False)

    main_h, child = find_render_target()
    tx, ty, tw, th = target_rect(child) if child else (0, 0, 997, 561)
    window = glfw.create_window(max(tw, 100), max(th, 100), "ClashLab 覆盖层", None, None)
    glfw.make_context_current(window)
    # P0-2：WM_CLOSE（任务栏/任务管理器/外部关闭）-> glfw should_close，主循环随之退出
    glfw.set_window_close_callback(window, lambda w: glfw.set_window_should_close(w, True))
    hwnd = glfw.get_win32_window(window)
    rt._hwnd = hwnd

    ex = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    ex |= WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex)

    imgui.create_context()
    io = imgui.get_io()
    io.set_ini_filename("")
    _load_cjk_font(rt, io, imgui)

    import OpenGL.GL as gl
    glfw.swap_interval(1)  # 垂直同步，封顶 ~60fps，避免忙等空转
    renderer = GlfwRenderer(window)
    # 性能打点（CLASH_PERF=1 开启；关闭时 begin/attach_hooks 均为 no-op）
    _perf.begin(root)
    _perf.attach_hooks()
    # 鼠标分层取证：链上 renderer 的 button callback，记录 WM_LBUTTONDOWN 是否到达 GLFW
    _glfw_btn_cb = renderer.mouse_button_callback
    def _dbg_btn_cb(win, button, action, mods):
        try:
            rt.log(f"[mouse-dbg] glfw button btn={button} action={action}")
        except Exception:
            pass
        _glfw_btn_cb(win, button, action, mods)
    glfw.set_mouse_button_callback(window, _dbg_btn_cb)
    ctx = _Ctx(rt)

    prev = {"mode": "HUD", "last_click": None, "t_restore": None, "visible": None}
    start_mode = str(cfg.get("mode", "HUD")).upper()
    if start_mode in ("PANEL", "HUD"):
        rt.request_mode(start_mode)
    always_on_top = bool(cfg.get("always_on_top", False))
    prev["monitor"] = None
    fps_rows = []
    t0 = time.perf_counter()
    prev_t = time.perf_counter()
    frame_n = 0
    main_h, child = find_render_target()
    rt.log(f"overlay loop start; start_mode={rt.state.mode}; always_on_top={always_on_top}")

    while not glfw.window_should_close(window):
        glfw.poll_events()
        if rt.exit_request:  # P0-2：面板退出按钮
            rt.log("exit_request -> break main loop")
            break
        frame_n += 1
        ft0 = time.perf_counter()
        _perf.frame_begin(frame_n, rt.state.mode)

        # 优化1：句柄缓存，IsWindow(child) 失效才全量重枚举（去掉每 30 帧盲枚举）
        main_h, child = get_render_target()

        # 优化4：隐藏态（上一帧 show=False）只在每 30 帧探测帧做 monitor/前台检测/
        # 几何取矩形，其余帧沿用上一帧 show=False，跳过这三段 win32 系统调用；
        # 可见态每帧全量（跟随前台/守卫/几何不能降频）。
        prev_hidden = prev["visible"] is False
        probe = (not prev_hidden) or frame_n % 30 == 1
        if probe:
            # ---- 主屏禁区守卫：渲染窗口在主显示器 → 强制隐藏，不响应显示/PANEL 请求 ----
            # 优化2：monitor 结果缓存 1/30 帧，同句柄不重复 MonitorFromWindow/GetMonitorInfo
            hmon, on_primary, rc_mon = get_render_monitor(child, frame_n)
            if hmon != prev.get("monitor"):
                rt.log(f"overlay monitor change -> monitor={hex(hmon) if hmon else None} "
                       f"primary={on_primary} rcMonitor={rc_mon}")
                prev["monitor"] = hmon
            rt._primary_blocked = bool(GUARD_PRIMARY_DISPLAY and on_primary and not allow_primary)

            # ---- 可见性策略：默认跟随前台；always_on_top 才常显；守卫优先于一切 ----
            fg = user32.GetForegroundWindow()
            fg_root = user32.GetAncestor(fg, GA_ROOT)
            fg_title = win32gui.GetWindowText(fg) or ""
            belongs = _fg_belongs_to_ld(fg_root, main_h)
            # PANEL 特判：面板激活后前台就是覆盖层自己，旧的 not-ldplayer-foreground
            # 隐藏会立刻把刚点开的面板藏掉；PANEL 期间不做该隐藏，ESC 回 HUD 后按原策略。
            panel_keep = rt.state.mode == "PANEL"
            show = (bool(child) and not rt._primary_blocked
                    and (always_on_top or belongs or panel_keep))
            if child:
                prev.pop("wait_shown", None)  # v9-①：目标窗回来，解除等待横幅态
        else:
            hmon, on_primary, rc_mon = prev.get("mon", (None, False, None))
            show = False
            fg_title = ""
        prev["mon"] = (hmon, on_primary, rc_mon)

        if show != prev["visible"]:
            if show:
                win32gui.ShowWindow(hwnd, SW_SHOWNOACTIVATE)
                rt.log(f"overlay SHOW fg={hex(fg)} title='{fg_title}' "
                       f"reason={'always-on-top' if always_on_top else ('panel-keep' if panel_keep else 'ldplayer-foreground')}")
            else:
                win32gui.ShowWindow(hwnd, SW_HIDE)
                if rt._primary_blocked:
                    rt.log(f"overlay HIDE reason=target-on-primary-display "
                           f"monitor={hex(hmon)} rect={rc_mon}")
                else:
                    rt.log(f"overlay HIDE fg={hex(fg)} title='{fg_title}' "
                           f"reason={'no-render-target' if not child else 'not-ldplayer-foreground'}")
            prev["visible"] = show

        # ---- 几何：HUD=客户区矩形（动态取，不写死）；PANEL=面板独立矩形（外置） ----
        # 优化4：隐藏非探测帧跳过 target_rect（ClientToScreen/GetClientRect）
        tx = ty = tw = th = 0
        if child and (probe or show):
            tx, ty, tw, th = target_rect(child)
            # v9-③：(tw,th) 变化立刻按新视口重建 Calib（归一化缩放），标注不清空不闪断
            pv = prev.get("vp")
            if pv and (abs(tw - pv[0]) > 1.0 or abs(th - pv[1]) > 1.0):
                rt._build_calib(tw, th)
                rt.log(f"viewport {pv[0]:.0f}x{pv[1]:.0f} -> {tw:.0f}x{th:.0f}; "
                       f"calib rebuilt (normalized scale, marks kept)")
                ratio = max(tw / pv[0], th / pv[1], pv[0] / tw, pv[1] / th)
                if ratio > 1.10 and prev.get("last_recalib_size") != (round(tw), round(th)):
                    prev["last_recalib_size"] = (round(tw), round(th))
                    rt.log("viewport 变化 >10%: 尝试一次自动重标定（失败归一化缩放兜底）")
                    rt.request_recalib()
            prev["vp"] = (tw, th)
            if rt.state.mode == "PANEL":
                # v9-④：缺省/auto -> 右→下→内全自动选择并进日志；仅显式指定读配置
                pref = str(rt.cfg.get("panel_position") or "auto").lower()
                if pref in ("", "default"):
                    pref = "auto"
                px, py, pw, ph, zone = _panel_place(tx, ty, tw, th, pref)
                # P2-5：只有 (pref, zone) 真的变了才记日志。旧实现把 WARN 放在
                # 该 if 之外，显式档位回退 inner 时**每帧刷一行**（实测日志膨胀）。
                key = (pref, zone)
                if key != prev.get("last_zone_key"):
                    prev["last_zone_key"] = key
                    prev["last_zone"] = zone
                    if pref == "auto":
                        rt.log(f"panel 位置自动选择 -> {zone}（右→下→内）")
                    elif zone != pref:
                        rt.log(f"[WARN] panel_position={pref} 放不下，回退 {zone}"
                               + ("（叠游戏内右侧 440 条带）" if zone == "inner" else ""))
                    else:
                        rt.log(f"panel_position={pref} -> {zone}")
            else:
                px, py, pw, ph, zone = tx, ty, tw, th, "hud"
            # P2-7：GetWindowRect 缓存 1/30 帧（静止时 swp_n 已为 0，仅余量清理）；
            # 句柄失效/模式切换由上层重探测，缓存只减系统调用，不影响目标比对。
            if frame_n % 30 == 1 or "_winrect" not in prev:
                prev["_winrect"] = win32gui.GetWindowRect(hwnd)
            wx, wy, wx2, wy2 = prev["_winrect"]
            if (wx, wy, wx2 - wx, wy2 - wy) != (px, py, pw, ph):
                win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST,
                                      int(px), int(py), int(pw), int(ph),
                                      win32con.SWP_NOACTIVATE)
                ex = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                rt.log(f"mode={rt.state.mode} rect=({px:.0f},{py:.0f},"
                       f"{pw:.0f}x{ph:.0f}) panel_w={pw:.0f} zone={zone} "
                       f"exstyle=0x{ex:08x}")
            rt._win_w, rt._win_h = float(pw), float(ph)

        # 热键边沿检测（F8 切模式 / F9 采集 / F12 重载 / F7 live / ESC 回 HUD）
        _poll_hotkeys(rt, window, prev)

        # 模式切换同帧处理 exstyle
        if rt.state.mode != prev["mode"]:
            _apply_mode_exstyle(hwnd, rt.state.mode, rt, prev)

        # 隐藏态：跳过清屏/绘制/交换，但保持轮询循环与热键；不计入呈现帧率
        # v9-①：无目标窗（找不到雷电）不退出不崩，落到等待横幅分支持续轮询
        wait = (not show) and (not child)
        if not show and not wait:
            prev_t = time.perf_counter()
            run_seconds = cfg.get("run_seconds")
            if run_seconds and time.perf_counter() - t0 >= float(run_seconds):
                break
            continue

        # 恢复 HUD 后首次点击命中时刻（测 ≤1 帧）
        if prev.get("t_restore") is not None:
            down = bool(io.mouse_down[0])
            if down and not prev.get("prev_down", False):
                t_click = time.perf_counter()
                dt_ms = (t_click - prev["t_restore"]) * 1000.0
                rt.log(f"first click after restore @ {t_click*1000:.3f}ms "
                       f"restore->click={dt_ms:.3f}ms")
                prev["t_restore"] = None
            prev["prev_down"] = down

        # 数据热重载请求
        if rt.reload_request:
            rt.reload_request = False
            reload(rt.state)
            rt._build_calib(*rt._calib_vp)
            rt.log("data reloaded (mtime)")

        # v9-⑥闭环：data_prep_request 消费者（表优先，无表抓帧+detect；自动≤2次/启动）
        if rt.data_prep_request:
            rt._consume_data_prep()

        # 清屏全透
        gl.glClearColor(0.0, 0.0, 0.0, 0.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        # v9-①：等待雷电启动分支——居中小横幅，持续轮询，不抢焦点不抓屏
        if wait:
            if prev.get("wait_shown") is not True:
                win32gui.ShowWindow(hwnd, SW_SHOWNOACTIVATE)
                prev["wait_shown"] = True
                rt.log("waiting: LDPlayerMainFrame 未找到，持续轮询等待启动")
            sw = user32.GetSystemMetrics(0)
            sh = user32.GetSystemMetrics(1)
            wx, wy = int((sw - 420) / 2), int((sh - 90) / 2)
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, wx, wy,
                                  420, 90, win32con.SWP_NOACTIVATE)

        # PANEL 态自喂鼠标（兜底通路，见 _feed_panel_mouse）；HUD 保持穿透不喂
        if rt.state.mode == "PANEL" and not wait:
            _feed_panel_mouse(rt, window, hwnd, io, prev)

        imgui.new_frame()
        dl = imgui.get_foreground_draw_list()
        _perf.build_begin()
        try:
            rows = _tactics_rows(rt)
            sel_idx = int(tactics.SEL.get("idx", 0))
            if wait:
                _draw_wait_banner(imgui, dl)
            elif rt.state.mode == "PANEL":
                # PANEL 窗口独立在游戏外：只画面板，不画 HUD 标注（任务1）
                _draw_panel_container(imgui, rt, ctx)
            else:
                # v9-②：calib 已按当前视口还原为客户区像素；draw 层内部按
                # 1280x720 虚拟基准再缩放，这里传虚拟尺寸避免二次缩放
                hud_draw.draw_marks(dl, rt.calib, rt.state.marks, 1280.0, 720.0)
                try:
                    from . import giant_arrow_hud
                    _gap = giant_arrow_hud.load_overlay_plan(rt.root)
                    if _gap:
                        giant_arrow_hud.draw_giant_arrow(dl, rt.calib, _gap, 1280.0, 720.0)
                except Exception:
                    pass
                # H4 引擎互斥：llm 只画策略点，local 只画 rank 点，绝不同帧共存；
                # 切引擎后分支互斥，旧标注下一帧即归零，不留残影
                if tactics.SEL.get("engine") == "llm":
                    plan_doc = _plan_doc(rt)
                    if plan_doc.get("phases"):  # schema v2 命中走新 phases 图层
                        # 现网无战斗时钟 -> t_now=None（phase_at_t 内部兜底不高亮），
                        # 不伪造时钟；后续有回放/测速时钟再传 rt.battle_clock
                        hud_draw.draw_plan_phases(
                            dl, rt.calib, plan_doc, 1280.0, 720.0, t_now=None,
                            show_threats=bool(tactics.SEL.get("show_threats", True)),
                            show_route=bool(tactics.SEL.get("show_route", True)))
                    else:  # 旧 v5 plan.json 无 phases，回退旧 marks 标注
                        hud_draw.draw_plan_marks(
                            dl, rt.calib, plan_doc.get("marks") or {}, 1280.0, 720.0,
                            show_threats=bool(tactics.SEL.get("show_threats", True)),
                            show_route=bool(tactics.SEL.get("show_route", True)))
                elif rows:
                    hud_draw.draw_important(dl, rt.calib, rows, sel_idx, 1280.0, 720.0)
                _draw_status_badge(imgui, rt, tw, th)
        except Exception as e:
            key = repr(e)[:120]
            if key not in prev.get("_seen_err", set()):
                prev.setdefault("_seen_err", set()).add(key)
                rt.log(f"draw frame error (skipped, once): {e!r}")
        _perf.build_end()

        _perf.submit_begin()
        renderer.process_inputs()
        imgui.render()
        # 关闭态不在此调用 get_draw_data（参数不求值额外 ImGui 调用）；
        # 开启态由 perf 内部取 draw data 统计 vtx/cmd
        _perf.collect_draw_data(imgui)
        renderer.render(imgui.get_draw_data())
        _perf.submit_end()
        _perf.swap_buffers(window, glfw)

        # FPS 采样：帧间隔 dt（秒），记录模式用于分组
        now_t = time.perf_counter()
        dt = now_t - prev_t
        prev_t = now_t
        if dt > 0:
            fps_rows.append((frame_n, dt * 1000.0, 1.0 / dt, now_t - t0, rt.state.mode))
            _perf.frame_end(now_t, dt * 1000.0, rt.state.mode,
                            win_rect=(wx, wy, wx2, wy2) if child else None,
                            target=(tx, ty, tw, th) if child else None)

        # 60fps 节流（显式 pacing；swap_interval 在本机 DWM 下不生效）
        nxt = prev.get("next_t")
        if nxt is None:
            nxt = now_t + 1.0 / float(cfg.get("fps_cap", 60))
        nxt += 1.0 / float(cfg.get("fps_cap", 60))
        sl = nxt - time.perf_counter()
        _perf.pace_sleep(sl)
        if sl <= 0:
            nxt = time.perf_counter()
        prev["next_t"] = nxt

        run_seconds = cfg.get("run_seconds")
        if run_seconds and time.perf_counter() - t0 >= float(run_seconds):
            break

    _perf.end_run()
    summary = _write_fps(root, fps_rows)
    rt.log(f"fps summary: {summary}")
    try:
        glfw.destroy_window(window)
        glfw.terminate()
    except Exception:
        pass
    rt.log("overlay runtime end")


def _load_cjk_font(rt, io, imgui):
    """msyh.ttc 直载（新 atlas 1.92 无 glyph_ranges 形参，ranges 机制已移除）。"""
    try:
        io.fonts.add_font_from_file_ttf(r"C:\Windows\Fonts\msyh.ttc", 18.0)
        rt.font_ready = True
        rt.log("CJK font msyh.ttc loaded (plain)")
    except Exception as e:
        io.fonts.add_font_default()
        rt.font_ready = False
        rt.log(f"CJK font fallback to default: {e}")


def _fmt_flags(ex: int) -> str:
    return (f"LAYERED={bool(ex & WS_EX_LAYERED)} "
            f"TRANSPARENT={bool(ex & WS_EX_TRANSPARENT)} "
            f"NOACTIVATE={bool(ex & WS_EX_NOACTIVATE)} "
            f"TOOLWINDOW={bool(ex & WS_EX_TOOLWINDOW)}")


def _expected_exstyle(mode: str) -> int:
    """PANEL：可点击可激活（LAYERED|TOOLWINDOW，无 TRANSPARENT/NOACTIVATE）；
    HUD：完全穿透不抢焦点（LAYERED|TRANSPARENT|NOACTIVATE|TOOLWINDOW）。"""
    if mode == "PANEL":
        return WS_EX_LAYERED | WS_EX_TOOLWINDOW
    return (WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW)


def _apply_mode_exstyle(hwnd, mode: str, rt, prev):
    """HUD<->PANEL 同帧切换：PANEL 可点击激活，HUD 穿透不抢焦；
    每次切换前后记 exstyle 十六进制与标志位，并断言目标态无累积错误。"""
    ex = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    before = f"0x{ex:08x} [{_fmt_flags(ex)}]"
    t_now = time.perf_counter()
    if mode == "PANEL":
        new = (ex & ~WS_EX_TRANSPARENT) & ~WS_EX_NOACTIVATE
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, new)
        # 不抢前台：SetForegroundWindow 会把雷电挤到后台；PANEL 可点击性由
        # exstyle（摘 TRANSPARENT/NOACTIVATE）+ 自喂鼠标通路保证，前台留给雷电。
        rt.log("panel: exstyle clickable; foreground not stolen (LDPlayer stays front)")
        rt.log(f"mode switch HUD->PANEL t={t_now*1000:.3f}ms "
               f"exstyle before={before} after=0x{new:08x} [{_fmt_flags(new)}]")
    else:
        new = _expected_exstyle("HUD")
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, new)
        prev["t_restore"] = t_now
        rt.log(f"mode switch PANEL->HUD t={t_now*1000:.3f}ms "
               f"exstyle before={before} after=0x{new:08x} [{_fmt_flags(new)}]")
    # 断言：回读目标标志位与期望一致，5 次循环无累积错误
    got = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    want = _expected_exstyle(mode)
    cycle = prev.get("exstyle_cycle", 0) + 1
    prev["exstyle_cycle"] = cycle
    match = (got & (WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW)) == want
    if match:
        rt.log(f"exstyle assert cycle={cycle} OK mode={mode} got=0x{got:08x}")
    else:
        rt.log(f"exstyle assert cycle={cycle} MISMATCH mode={mode} "
               f"want=0x{want:08x} got=0x{got:08x} [{_fmt_flags(got)}]")
    prev["mode"] = mode


def _async_key(vk: int) -> bool:
    return bool(user32.GetAsyncKeyState(vk) & 0x8000)


# ---------------------------------------------------------------- PANEL 自喂鼠标
# 背景：GLFW mouse_callback 仅在窗口 FOCUSED 时喂真实光标，否则喂 (-1,-1)；
# 覆盖层在 Windows 前台锁下拿不到键盘焦点，io.mouse_pos 停在 (-1,-1)，
# imgui 按钮永不 hover —— 这是 PANEL 点击失效的根因。兜底通路：PANEL 态每帧
# 用 GetCursorPos + GetAsyncKeyState(VK_LBUTTON/RBUTTON) 自己把光标/按键喂给
# imgui；HUD 态不调用，保持完全穿透。
VK_LBUTTON = 0x01
VK_RBUTTON = 0x02


class _POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


def _mouse_edge_dbg(rt, window, hwnd, btn, down, client_pt):
    """点击边沿取证（分层定位用）：光标是否落窗口内 / glfw 是否认为窗口获焦。"""
    try:
        import glfw
        pt = _POINT(client_pt.x, client_pt.y)
        user32.ClientToScreen(hwnd, ctypes.byref(pt))
        rx0, ry0, rx1, ry1 = win32gui.GetWindowRect(hwnd)
        inside = rx0 <= pt.x <= rx1 and ry0 <= pt.y <= ry1
        focused = bool(glfw.get_window_attrib(window, glfw.FOCUSED))
        rt.log(f"[mouse-dbg] {btn} {'down' if down else 'up'} "
               f"client=({client_pt.x},{client_pt.y}) win=({rx0},{ry0},{rx1},{ry1}) "
               f"inside={inside} glfw_focused={focused}")
    except Exception as e:
        rt.log(f"[mouse-dbg] edge log fail: {e!r}")


def _feed_panel_mouse(rt, window, hwnd, io, prev):
    """PANEL 态自喂鼠标：光标位置 + 左右键边沿喂 imgui（HUD 不调用）。

    失败不许静默（20:38 批 AttachThreadInput 兜底"失败记日志"的等价保证）：
    GetCursorPos / ScreenToClient 失败、或光标落在客户区外，各记一次性日志，
    成功后复位节流位，下次失败可再记。
    """
    pt = _POINT()
    if not user32.GetCursorPos(ctypes.byref(pt)):
        if not prev.get("feed_gcp_fail"):
            rt.log("[mouse-feed] GetCursorPos failed in PANEL; mouse feed suspended")
            prev["feed_gcp_fail"] = True
        return
    if not user32.ScreenToClient(hwnd, ctypes.byref(pt)):
        if not prev.get("feed_stc_fail"):
            rt.log("[mouse-feed] ScreenToClient failed (cursor outside client / resolution changed); mouse feed suspended")
            prev["feed_stc_fail"] = True
        return
    prev.pop("feed_gcp_fail", None)
    prev.pop("feed_stc_fail", None)
    # 光标落在客户区外（分辨率变化 / 窗口移动错位）：记一次，不阻断喂入
    # （imgui 自行忽略窗外坐标；此处仅作错位取证）
    rx0, ry0, rx1, ry1 = win32gui.GetWindowRect(hwnd)
    if pt.x < 0 or pt.y < 0 or pt.x > (rx1 - rx0) or pt.y > (ry1 - ry0):
        if not prev.get("feed_outside"):
            rt.log(f"[mouse-feed] cursor outside client rect client=({pt.x},{pt.y}) "
                   f"win=({rx0},{ry0},{rx1},{ry1}); feed continues")
            prev["feed_outside"] = True
    else:
        prev.pop("feed_outside", None)
    io.add_mouse_pos_event(float(pt.x), float(pt.y))
    left = bool(user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000)
    right = bool(user32.GetAsyncKeyState(VK_RBUTTON) & 0x8000)
    prev_l = prev.get("pm_l", False)
    prev_r = prev.get("pm_r", False)
    if left != prev_l:
        io.add_mouse_button_event(0, left)
        _mouse_edge_dbg(rt, window, hwnd, "left", left, pt)
    if right != prev_r:
        io.add_mouse_button_event(1, right)
        _mouse_edge_dbg(rt, window, hwnd, "right", right, pt)
    prev["pm_l"], prev["pm_r"] = left, right


# ---------------------------------------------------------------- 热键轮询（绑键表驱动）

def _keys_vkmap(rt, prev):
    """overlay_keys.json mtime 缓存：改动即热重载（不重启），返回 vk_map。"""
    path = keybind.bind_path(rt.root)
    try:
        mt = os.stat(path).st_mtime
    except OSError:
        mt = 0.0
    if prev.get("keys_mtime") != mt or prev.get("keys_root") != rt.root:
        try:
            keybind.load(rt.root)
            for w in keybind.pop_warns():
                rt.log(f"[keys] {w}")
        except Exception as e:
            # v9-⑤：绑键表读取任何异常都回退默认，绝不崩出循环
            rt.log(f"[keys] load fail -> default bindings: {e}")
        prev["keys_mtime"] = mt
        prev["keys_root"] = rt.root
    return keybind.vk_map()


def _start_ocr_job(rt) -> None:
    """F6：抓当前帧 → OCR → ClashKing API → 写 out/ocr_latest.json（后台线程，不阻塞渲染）。"""
    import threading

    def worker():
        try:
            frame = rt._default_grab()
            if frame is None:
                rt.log("OCR: 抓帧失败（游戏窗口不可用）")
                return
            from clashlab import ocr_job
            payload = ocr_job.run_ocr(rt.root, frame)
            rt.ocr_line = payload.get("line") or ""
            rt.log("OCR: " + rt.ocr_line)
        except Exception as e:  # noqa: BLE001 - 热键失败只记录，不崩面板
            rt.log("OCR 失败: %r" % (e,))

    threading.Thread(target=worker, daemon=True).start()


def _dispatch_action(rt, action: str) -> None:
    """绑键动作分发：未绑定动作不进 vk_map，自动跳过。"""
    if action == "ocr_opponent":
        try:
            _start_ocr_job(rt)
        except Exception as e:  # noqa: BLE001
            rt.log("ocr request fail: %r" % (e,))
    elif action == "toggle_mode":
        # 主屏守卫拦截：主屏上禁止切出 PANEL（HUD 也被强制隐藏）
        if getattr(rt, "_primary_blocked", False):
            rt.log("toggle_mode ignored: target-on-primary-display guard blocks PANEL")
            return
        rt.request_mode("PANEL" if rt.state.mode == "HUD" else "HUD")
        rt.log(f"hotkey toggle_mode -> {rt.state.mode}")
    elif action == "capture":
        rt.farm_request = "stop" if rt.farm_request == "start" else "start"
        rt.log(f"hotkey capture -> {rt.farm_request}")
    elif action == "live":
        rt.state.live = not rt.state.live
        rt.log(f"hotkey live -> {rt.state.live}")
    elif action == "reload":
        rt.request_reload()
        rt.log("hotkey reload requested")
    elif action == "back_hud" and rt.state.mode == "PANEL":
        rt.request_mode("HUD")
        rt.log("hotkey back_hud -> HUD")


def _poll_hotkeys(rt, window, prev):
    # 全局热键：GetAsyncKeyState 不要求窗口焦点（NOACTIVATE 窗口收不到 glfw 键事件）；
    # 键表来自 config/overlay_keys.json（keys.vk_map()），无任何硬编码键。
    vkmap = _keys_vkmap(rt, prev)
    dbg = os.environ.get("CLASHLAB_KEYDBG") == "1"
    for vk, action in vkmap.items():
        raw = user32.GetAsyncKeyState(vk)
        now = bool(raw & 0x8000)
        was = prev.get(f"hk:{action}", False)
        if dbg:
            rt.log(f"[keydbg] vk=0x{vk:02x} raw=0x{raw & 0xFFFF:04x} action={action} edge={'DOWN' if now and not was else ('up' if not now else 'hold')}")
        if now and not was:
            _dispatch_action(rt, action)
        prev[f"hk:{action}"] = now


def _draw_panel_container(imgui, rt, ctx):
    """PANEL 容器：只负责背景板，文字交给 pages.draw_panel 独占绘制。"""
    from . import theme
    io = imgui.get_io()
    W, H = io.display_size.x, io.display_size.y
    # 外置后窗口即面板：panel_w 直接等于窗口宽 tw（旧比例公式已删）；
    # 底板铺满整个窗口，alpha 0.97 禁止透出后面窗口
    panel_w = W
    px, py = 0.0, 0.0
    # 底色必须走 background draw list：foreground 会在窗口之后合成，会把面板文字压暗
    dl = imgui.get_background_draw_list()
    # 竖向微渐变：顶部略亮、底部略沉，避免整块死板纯色
    _u = imgui.color_convert_float4_to_u32
    _bg = theme.PANEL_BG
    _top = theme._lift(_bg, 1.16)
    _bot = theme._lift(_bg, 0.88)
    try:
        dl.add_rect_filled_multi_color(
            imgui.ImVec2(px, py), imgui.ImVec2(W, H),
            _u(imgui.ImVec4(*_top)), _u(imgui.ImVec4(*_top)),
            _u(imgui.ImVec4(*_bot)), _u(imgui.ImVec4(*_bot)))
    except TypeError:
        # 不同 imgui_bundle 版本签名不一致：退化为纯色，避免 draw frame error
        dl.add_rect_filled(imgui.ImVec2(px, py), imgui.ImVec2(W, H), _u(imgui.ImVec4(*_bg)))
    # 顶部琥珀强调条（左亮右暗，像一条细高光）
    _bar_w = 3.0
    _accent = theme.ACCENT
    dl.add_rect_filled_multi_color(
        imgui.ImVec2(px, py), imgui.ImVec2(W, py + _bar_w),
        _u(imgui.ImVec4(*_accent)), _u(imgui.ImVec4(_accent[0], _accent[1], _accent[2], 0.35)),
        _u(imgui.ImVec4(_accent[0], _accent[1], _accent[2], 0.35)), _u(imgui.ImVec4(*_accent)))
    # 内高光（1px）+ 外描边
    dl.add_line(imgui.ImVec2(px, py + _bar_w), imgui.ImVec2(W, py + _bar_w),
                _u(imgui.ImVec4(1.0, 1.0, 1.0, 0.06)), 1.0)
    dl.add_rect(imgui.ImVec2(px, py), imgui.ImVec2(W, H),
                col=_u(imgui.ImVec4(*theme.PANEL_BORDER)),
                rounding=0.0, thickness=1.5)
    if not getattr(rt, "_panel_logged", False):
        rt._panel_logged = True
        # P1-3：底板 rect 与窗口 rect 对证——两者必须相等，否则边缘透光（终端文字透进面板）
        try:
            rx0, ry0, rx1, ry1 = win32gui.GetWindowRect(rt._hwnd)
            win_w, win_h = rx1 - rx0, ry1 - ry0
            equal = abs(W - win_w) <= 1 and abs(H - win_h) <= 1
        except Exception as e:
            win_w = win_h = -1
            equal = False
            rt.log(f"PANEL rect check GetWindowRect fail: {e!r}")
        rt.log(f"PANEL rect check: bg=({px:.0f},{py:.0f},{W:.0f}x{H:.0f}) "
               f"win=({win_w}x{win_h}) equal={equal}")
        rt.log(f"PANEL draw container first frame: panel_w={panel_w:.0f} W={W:.0f} H={H:.0f}")
    # 注意：标签条/状态行/步骤提示一律由 pages.draw_panel 绘制。此前这里也用
    # foreground draw list 画过一遍「研究/采集/设置」和步骤行，与 pages 的按钮标签
    # 落在同一坐标上，两层文字相互叠压（实测呈现为"研究中夹着 research"的字形错乱）。
    # 现在这里只画背景，pages 缺席时才走兜底文字。
    try:
        from . import pages
        pages.draw_panel(ctx, rt.state)
    except ImportError:
        _panel_fallback(imgui, dl, px, "PANEL 未就绪：pages.draw_panel 缺失")
    except Exception as e:
        rt.log(f"pages.draw_panel error: {e!r}")
        _panel_fallback(imgui, dl, px, f"PANEL 异常：{e}")


def _panel_fallback(imgui, dl, px, msg):
    """pages 缺席/异常时的兜底文字（同一时刻只有这一份，不会叠字）。"""
    tx = px + 12.0
    for label in ("研究 research", "采集 collect", "设置 setting"):
        dl.add_text(imgui.ImVec2(tx, 10.0),
                    imgui.color_convert_float4_to_u32(imgui.ImVec4(0.6, 0.62, 0.65, 1.0)),
                    label)
        tx += 92.0
    dl.add_text(imgui.ImVec2(px + 16.0, 56.0),
                imgui.color_convert_float4_to_u32(imgui.ImVec4(0.90, 0.36, 0.32, 1.0)),
                msg)


# ---------------------------------------------------------------- P2-4 首启角标
FIRST_RUN_HINT_DWELL_S = 6.0   # 可见帧累计展示满 6s 才落 flag（旧实现只闪 1 帧≈17ms）
FIRST_RUN_FLAG_NAME = ".first_run_done"


def first_run_flag_path(root: str) -> str:
    return os.path.join(root, "out", "overlay", FIRST_RUN_FLAG_NAME)


def _first_run_flag_path(root: str) -> str:
    """兼容旧名（历史代码/外部脚本引用）。"""
    return first_run_flag_path(root)


def mark_first_run_done(root: str) -> bool:
    """原子落首启 flag（.tmp -> flush+fsync -> os.replace）；失败返回 False 不抛。"""
    path = first_run_flag_path(root)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S first-run hint shown\n"))
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        return True
    except Exception:
        return False


def _has_layout_data(state) -> bool:
    """首启角标的「已有阵型数据就不打扰」判定（口径与旧实现一致）。"""
    return (bool(getattr(state, "marks", None))
            or bool(getattr(state, "study_info", None))
            or bool(getattr(state, "candidates", None)))


class FirstRunHint:
    """P2-4：首启角标一次性状态机（纯逻辑 + 时钟注入，离线可单测）。

    旧实现（原 _draw_status_badge 内联块）在**画角标的同一帧**就写 .first_run_done，
    60fps 下只闪 1 帧（≈17ms），用户根本看不见——实测 _p2b/firstrun_baseline_run1.json：
    flag 与窗口首帧同一采样刻出现（Δ<50ms），0.6–7.0s 五张截图全无角标。
    新实现：只在**可见帧**累计展示满 dwell_s 秒后落 flag；落盘成功即永久关闭；
    落盘失败继续提示（每 retry_s 重试一次），不静默丢掉首启提示。
    """

    def __init__(self, root: str, dwell_s: float = FIRST_RUN_HINT_DWELL_S,
                 retry_s: float = 1.0):
        self.root = os.path.abspath(root)
        self.dwell_s = float(dwell_s)
        self.retry_s = float(retry_s)
        self.shown_s = 0.0          # 可见帧累计展示时长
        self._last_t = None
        self._next_write_t = 0.0
        self._done = os.path.exists(first_run_flag_path(self.root))
        self.wrote = False          # 本次运行是否成功落盘（供日志）

    @property
    def done(self) -> bool:
        return self._done

    def tick(self, now: float, has_data: bool) -> bool:
        """每**可见帧**调一次（now=time.perf_counter）；返回 True=本帧要画角标。
        has_data=True：已有阵型数据，不提示也不落 flag（保留「无数据首启」语义）。"""
        if self._done:
            return False
        if has_data:
            self._last_t = None
            return False
        if self._last_t is not None:
            dt = now - self._last_t
            if dt > 0:
                self.shown_s += min(dt, 0.5)  # 卡顿/挂起时钳制，防一帧跳满
        self._last_t = now
        if self.shown_s >= self.dwell_s and now >= self._next_write_t:
            if mark_first_run_done(self.root):
                self._done = True
                self.wrote = True
                return False
            self._next_write_t = now + self.retry_s
        return True


def _draw_first_run_hint(imgui, rt, dl) -> None:
    """P2-4：首启角标（无阵型数据时提示「按 Insert → 自动采集」）。
    一次性语义见 FirstRunHint；本函数只负责可见帧驱动与绘制。"""
    try:
        hint = getattr(rt, "first_run_hint", None)
        if hint is None:
            hint = FirstRunHint(rt.root)
            rt.first_run_hint = hint
        if hint.tick(time.perf_counter(), _has_layout_data(rt.state)):
            fr = "按 Insert 打开面板 → 点「自动采集」"
            # P2-6/C10：原左上 (8,30) 实测压等级徽章/姓名横幅 5104 px²；改到顶部
            # 中央空带第 4 行水平居中。文案/字号/一次性语义不变，只改落点。
            try:
                _W = float(imgui.get_io().display_size.x) or 1280.0
            except Exception:
                _W = 1280.0
            _w = imgui.calc_text_size(fr).x
            _x0 = max(8.0, (_W - (_w + 16.0)) / 2.0)
            _y = _HUD_BADGE_ROW_Y["first_run"]
            dl.add_rect_filled(imgui.ImVec2(_x0, _y - 4.0),
                               imgui.ImVec2(_x0 + _w + 16.0, _y + 18.0),
                               col=imgui.color_convert_float4_to_u32(
                                   imgui.ImVec4(0.20, 0.15, 0.05, 0.85)), rounding=4.0)
            dl.add_text(imgui.ImVec2(_x0 + 8.0, _y),
                        imgui.color_convert_float4_to_u32(
                            imgui.ImVec4(0.91, 0.64, 0.24, 1.0)), fr)
            if not getattr(rt, "_first_run_logged", False):
                rt._first_run_logged = True
                rt.log(f"first-run hint visible (dwell {hint.dwell_s:.1f}s -> flag)")
        elif hint.done and hint.wrote and not getattr(rt, "_first_run_done_logged", False):
            rt._first_run_done_logged = True
            rt.log(f"first-run hint marked done -> {first_run_flag_path(rt.root)} "
                   f"(shown {hint.shown_s:.1f}s)")
    except Exception:
        pass


def _draw_wait_banner(imgui, dl):
    """v9-①：找不到雷电时的居中小横幅（不抢焦点、不抓屏、持续轮询）。"""
    msg = "等待雷电模拟器启动…"
    sub = "自动查找 LDPlayerMainFrame，无需手动配置"
    c_bg = imgui.color_convert_float4_to_u32(imgui.ImVec4(0.10, 0.12, 0.15, 0.92))
    c_txt = imgui.color_convert_float4_to_u32(imgui.ImVec4(0.91, 0.64, 0.24, 1.0))
    c_sub = imgui.color_convert_float4_to_u32(imgui.ImVec4(0.62, 0.66, 0.70, 1.0))
    dl.add_rect_filled(imgui.ImVec2(0.0, 0.0), imgui.ImVec2(420.0, 90.0),
                      col=c_bg, rounding=8.0)
    dl.add_text(imgui.ImVec2(24.0, 26.0), c_txt, msg)
    dl.add_text(imgui.ImVec2(24.0, 54.0), c_sub, sub)


# ---------------------------------------------------------------- P2-6/C10 角标安全区
# 实测自实机帧（out/overlay/_p2c/c10_native_regions.json）：主世界与部落战侦察视图的
# 四个角都被游戏原生 UI 占用——左上等级/部落信息、右上资源条、左下战斗/战争地图钮、
# 右下建造/回放。旧落点实测压盖 1458–5104 px²/元素（c10_overlap_before.json）。
# 因此角标不再贴角：统一改到「顶部中央空带」按行水平居中；「Insert 打开面板」改到
# 「底部中央空带」水平居中。只改落点，字号(18)/配色/文案一律不动（红线：不许缩字号）。
_HUD_BADGE_ROW_Y = {"live": 8.0, "threat": 30.0, "view_warn": 52.0,
                    "first_run": 74.0, "prep_fail": 96.0}


def _hud_center_x(W: float, w: float) -> float:
    """P2-6/C10：把宽 w 的元素水平居中（左内边距至少 8px）。"""
    return max(8.0, (float(W) - float(w)) / 2.0)


def _draw_status_badge(imgui, rt, W, H):
    dl = imgui.get_foreground_draw_list()

    def _u(rgba):
        return imgui.color_convert_float4_to_u32(imgui.ImVec4(*rgba))

    def _top_text(text, row, rgba):
        tw = imgui.calc_text_size(text).x
        dl.add_text(imgui.ImVec2(_hud_center_x(W, tw), _HUD_BADGE_ROW_Y[row]),
                    _u(rgba), text)

    def _top_bar(text, row, bg_rgba, fg_rgba):
        w = imgui.calc_text_size(text).x
        x0 = max(8.0, (float(W) - (w + 16.0)) / 2.0)
        y = _HUD_BADGE_ROW_Y[row]
        dl.add_rect_filled(imgui.ImVec2(x0, y - 4.0),
                           imgui.ImVec2(x0 + w + 16.0, y + 18.0),
                           col=_u(bg_rgba), rounding=4.0)
        dl.add_text(imgui.ImVec2(x0 + 8.0, y), _u(fg_rgba), text)

    # HUD live 状态角标（原右上 W-150,8 -> 顶部中央空带第 1 行）
    text = f"HUD  live={'ON' if rt.state.live else 'dry'}"
    _top_text(text, "live", (0.95, 0.77, 0.32, 1.0))
    # v6-C10：HUD「Insert 打开面板」不可点提示（原右下 H-22 压建造按钮 -> 底部中央空带）
    hint = "Insert 打开面板"
    hw = imgui.calc_text_size(hint).x
    dl.add_text(imgui.ImVec2(_hud_center_x(W, hw), H - 22.0),
                _u((0.62, 0.66, 0.70, 0.85)), hint)
    # v5：LLM 引擎 HUD 不可点状态角标「威胁n·路线开/关」（原左上 8,8 -> 第 2 行）
    if tactics.SEL.get("engine") == "llm":
        try:
            mk = (_plan_doc(rt).get("marks") or {})
            nt = len(mk.get("threats") or [])
            nr = len(mk.get("route") or [])
            if nt or nr:
                rt_badge = f"威胁{nt}·路线{'开' if tactics.SEL.get('show_route', True) else '关'}"
                _top_text(rt_badge, "threat", (0.227, 0.651, 0.788, 1.0))
        except Exception:
            pass
    # v9-⑦ / P2-4：首启角标（一次性）。逻辑全在 FirstRunHint、绘制在
    # _draw_first_run_hint；此处只留一行调用，便于 p2-render-owner 改 C10 角标避让。
    _draw_first_run_hint(imgui, rt, dl)
    # v9-⑥闭环：自动采集失败琥珀条（原左上 8,54 -> 第 5 行）
    dp_msg = getattr(rt, "data_prep_msg", ("neutral", ""))
    if dp_msg and dp_msg[1]:
        _top_bar(dp_msg[1], "prep_fail", (0.20, 0.15, 0.05, 0.85),
                 (0.91, 0.64, 0.24, 1.0))
    # P1-6：低干扰「视角可能已变」角标（原左上 8,8 -> 第 3 行，设置页可关；禁 F11 入口）
    if getattr(rt.state, "view_warn", False):
        _top_bar("视角可能已变 · 面板「重新对位」", "view_warn",
                 (0.20, 0.15, 0.05, 0.85), (0.91, 0.64, 0.24, 1.0))


def _write_fps(root, rows):
    """呈现帧率：仅统计可见绘制帧；按模式分组报 fps mean/P1/min 与帧时间 p50/p99。"""
    out = os.path.join(root, "out", "overlay", "fps.csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    try:
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["frame", "dt_ms", "fps", "wall_s", "mode"])
            for n, dt, fps, wall, mode in rows:
                w.writerow([n, round(dt, 3), round(fps, 2), round(wall, 3), mode])
    except Exception as e:
        print("fps write fail:", e)

    import numpy as np
    import json as _json
    by_mode: dict[str, list] = {}
    for n, dt, fps, wall, mode in rows:
        by_mode.setdefault(mode, []).append((dt, fps))

    summary = {"frames": len(rows), "groups": {}}
    for mode, items in by_mode.items():
        dts = np.array([i[0] for i in items])
        fpsv = np.array([i[1] for i in items])
        g = {
            "frames": len(items),
            "fps_mean": round(float(fpsv.mean()), 2),
            "fps_p1": round(float(np.percentile(fpsv, 1)), 2),
            "fps_min": round(float(fpsv.min()), 2),
            "frame_ms_p50": round(float(np.percentile(dts, 50)), 3),
            "frame_ms_p99": round(float(np.percentile(dts, 99)), 3),
        }
        summary["groups"][mode] = g
    with open(os.path.join(os.path.dirname(out), "fps_summary.json"), "w", encoding="utf-8") as f:
        _json.dump(summary, f, ensure_ascii=False, indent=2)
    return summary


def _self_check(rt, seconds: float) -> None:
    """不可见自检：数据加载、Calib 构造、marks 结构核对，定时退出。"""
    rt.log("self-check mode (invisible) start")
    reload(rt.state)
    rt._build_calib()
    marks = rt.state.marks
    rt.log(f"marks keys={list(marks.keys())} "
           f"marks={len(marks.get('marks') or [])} pins={len(marks.get('pins') or [])} "
           f"circles={len(marks.get('circles') or [])} steps={len(marks.get('steps') or [])}")
    if rt.calib is not None:
        for g in [(32, 22), (10, 27), (7, 25)]:
            x, y = rt.calib.tile_to_px(*g)
            rt.log(f"calib tile {g} -> px ({x:.1f},{y:.1f})")
    # 断连/缺文件韧性：再次 reload 不崩
    reload(rt.state)
    rt.log(f"self-check done in {seconds}s (no window shown)")
