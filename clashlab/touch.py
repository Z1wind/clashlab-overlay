# -*- coding: utf-8 -*-
"""雷电模拟器点击/触控模块。

三条通道按优先级：
1. mouse_sendinput —— SendInput 绝对坐标移动 + 左键按下/抬起（走 Windows 输入栈，
   依赖雷电「鼠标映射触摸」）。
2. mouse_postmsg  —— PostMessage(WM_LBUTTONDOWN/UP) 到渲染子窗口（免前台，备选）。
3. adb            —— `input tap`（慢但确定），前两条失败时自动降级。

坐标：渲染坐标系 = adb screencap 的 1280x720 帧坐标；渲染子窗口屏幕矩形在每次
序列开始前实时 GetWindowRect 重测。格<->像素只经 clashlab.geo.Calib。

安全：adb 掉线/雷电关闭/断网不抛未捕获异常，全部落到 result dict 与 clicks.log；
live=False 时只记录不下发。

桌面锁：每次点击序列开始前检查 out/overlay/_desktop_lock.txt；有效期内最长等 180s，
等不到则跳过本轮（失败不计入成功率）。
"""
from __future__ import annotations

import ctypes
import json
import os
import re
import subprocess
import threading
import time
from ctypes import wintypes
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Sequence, Tuple

import win32api
import win32con
import win32gui
import win32process

# ---------------------------------------------------------------- 路径常量
_PKG_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(_PKG_DIR)
OVERLAY_DIR = os.environ.get("CLASHLAB_OVERLAY_DIR",
                             os.path.join(PROJECT_ROOT, "out", "overlay"))
CLICK_LOG = os.path.join(OVERLAY_DIR, "clicks.log")
LOCK_FILE = os.path.join(OVERLAY_DIR, "_desktop_lock.txt")

# 进程 DPI 感知（per-monitor v2），保证 GetWindowRect 返回物理像素，与 SetCursorPos 对齐
try:
    ctypes.windll.user32.SetProcessDpiAwarenessContext(-4)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

user32 = ctypes.windll.user32

# 命名锚点（1280x720 渲染坐标系；未验证锚点带 ?）
ANCHORS: Dict[str, Tuple[float, float]] = {
    "store": (1170, 645),
    "battle": (88, 645),
    "m_battle": (75, 635),
    "m_search": (197, 535),
    "attack_close": (1088, 133),
    "confirm_close": (1237, 90),
    "find": (951, 474),
    "edit_army": (421, 570),
    "scout_back": (64, 44),      # ? 未验证
    "scout_attack": (1150, 640),  # ? 未验证
}

RENDER_W, RENDER_H = 1280.0, 720.0
CST = timezone(timedelta(hours=8))


def _iso() -> str:
    return datetime.now(CST).isoformat(timespec="milliseconds")


class LdTouch:
    """雷电触控客户端。

    hwnd: 渲染子窗口句柄（None 则按类名 RenderWindow/TheRender 自动找）。
    adb_serial: adb 序列号，默认 127.0.0.1:5555。
    live: False 时只写日志不真正下发（dry-run）。
    """

    METHODS = ("mouse_sendinput", "mouse_postmsg", "adb")

    def __init__(self, hwnd: Optional[int] = None,
                 adb_serial: str = "127.0.0.1:5555",
                 live: bool = True,
                 adb_path: str = r"E:\leidian\LDPlayer9\adb.exe",
                 log_path: str = CLICK_LOG,
                 auto_foreground: bool = True,
                 allow_primary: bool = False):
        self.live = bool(live)
        self.adb_serial = adb_serial
        self.adb_path = adb_path
        self.log_path = log_path
        self.auto_foreground = auto_foreground
        # 主屏禁区守卫：默认硬拒绝渲染窗落在主显示器的一切下发；--allow-primary 才放行
        self.allow_primary = bool(allow_primary)
        self.marks: List[dict] = []
        self.rows: List[dict] = []
        self._lock = threading.Lock()
        os.makedirs(OVERLAY_DIR, exist_ok=True)
        # 找渲染窗口
        self.render_hwnd = int(hwnd) if hwnd else self._find_render_window()
        self.main_hwnd = self._find_main_frame()
        self._last_rect: Optional[Tuple[int, int, int, int]] = None
        self._closed = False

    # ------------------------------------------------------------ 窗口发现
    @staticmethod
    def _find_by_class(classnames: Sequence[str], title_contains: str = "") -> Optional[int]:
        found = []

        def cb(hwnd, _):
            cn = win32gui.GetClassName(hwnd)
            if cn in classnames:
                if title_contains and title_contains not in win32gui.GetWindowText(hwnd):
                    return True
                found.append(hwnd)
            return True

        win32gui.EnumWindows(cb, None)
        if not found:
            # 也搜子窗口（RenderWindow 是子窗）
            def cb_top(hwnd, _):
                if win32gui.GetClassName(hwnd) == "LDPlayerMainFrame":
                    kids = []
                    def cc(ch, _):
                        kids.append(ch)
                        return True
                    win32gui.EnumChildWindows(hwnd, cc, None)
                    for ch in kids:
                        if win32gui.GetClassName(ch) in classnames:
                            found.append(ch)
                return True
            win32gui.EnumWindows(cb_top, None)
        return found[0] if found else None

    def _find_render_window(self) -> Optional[int]:
        # 先在 LDPlayerMainFrame 的子窗里找 RenderWindow/TheRender
        main = self._find_by_class(["LDPlayerMainFrame"])
        if main:
            kids = []
            def cc(ch, _):
                kids.append(ch)
                return True
            win32gui.EnumChildWindows(main, cc, None)
            for ch in kids:
                if win32gui.GetClassName(ch) == "RenderWindow":
                    return ch
            for ch in kids:
                if win32gui.GetWindowText(ch) == "TheRender":
                    return ch
        return self._find_by_class(["RenderWindow"])

    def _find_main_frame(self) -> Optional[int]:
        return self._find_by_class(["LDPlayerMainFrame"])

    # ------------------------------------------------------------ 桌面锁
    def _lock_check(self, seq_name: str) -> str:
        """返回 'proceed' / 'wait_done' / 'skip'。过期锁记警告后 proceed。"""
        if not os.path.exists(LOCK_FILE):
            return "proceed"
        try:
            raw = open(LOCK_FILE, "r", encoding="utf-8", errors="ignore").read()
        except Exception as e:
            self._log_raw(f"LOCK read error {e}; proceed")
            return "proceed"
        ts = self._parse_iso(raw)
        est = self._parse_est(raw)
        now = datetime.now(CST)
        if ts is None:
            self._log_raw(f"LOCK unparsable; proceed: {raw[:120]}")
            return "proceed"
        expiry = ts + timedelta(seconds=est + 60)  # 60s 宽限
        if now > expiry:
            self._log_raw(f"LOCK STALE occupant_ts={ts.isoformat()} est={est}s; warning, proceed")
            return "proceed"
        # 有效期内：等待最长 180s
        deadline = time.time() + 180
        while time.time() < deadline:
            time.sleep(2)
            if not os.path.exists(LOCK_FILE):
                self._log_raw(f"LOCK released before seq={seq_name}; proceed")
                return "wait_done"
            try:
                raw2 = open(LOCK_FILE, "r", encoding="utf-8", errors="ignore").read()
            except Exception:
                raw2 = ""
            ts2 = self._parse_iso(raw2)
            if ts2 is None or now > ts2 + timedelta(seconds=est + 60):
                self._log_raw(f"LOCK turned stale during wait; proceed")
                return "wait_done"
        self._log_raw(f"LOCK busy >180s at seq={seq_name}; skip this round (not counted)")
        return "skip"

    @staticmethod
    def _parse_iso(raw: str) -> Optional[datetime]:
        m = re.search(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)", raw)
        if not m:
            return None
        s = m.group(1).replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=CST)
            return dt.astimezone(CST)
        except Exception:
            return None

    @staticmethod
    def _parse_est(raw: str) -> int:
        m = re.search(r"(?:est[_ ]?sec|预计占用|est)[:=\s]*(\d+)", raw, re.I)
        return int(m.group(1)) if m else 60

    # ------------------------------------------------------------ 日志
    def _log_raw(self, line: str) -> None:
        os.makedirs(OVERLAY_DIR, exist_ok=True)
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(f"{_iso()} {line}\n")

    def _log_click(self, row: dict) -> None:
        self.rows.append(row)
        os.makedirs(OVERLAY_DIR, exist_ok=True)
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    # ------------------------------------------------------------ 几何
    def render_rect(self) -> Optional[Tuple[int, int, int, int]]:
        """渲染子窗口客户区物理屏幕矩形 (l,t,r,b)。

        口径：RenderWindow 的 GetClientRect + ClientToScreen（客户区层），
        GetWindowRect 仅作兜底。实测本机 RenderWindow 无边框，两者重合。
        黑边由 _margins 记录（左/上偏移与客户区内画面偏移）。
        """
        hwnd = self.render_hwnd
        if not hwnd or not win32gui.IsWindow(hwnd):
            self.render_hwnd = self._find_render_window()
            hwnd = self.render_hwnd
        if not hwnd:
            return None
        try:
            ox, oy = win32gui.ClientToScreen(hwnd, (0, 0))
            cw, ch = win32gui.GetClientRect(hwnd)[2:]
            rect = (ox, oy, ox + cw, oy + ch)
        except Exception:
            rect = win32gui.GetWindowRect(hwnd)
        self._last_rect = rect
        return rect

    # ------------------------------------------------------------ 主屏禁区守卫
    MONITORINFOF_PRIMARY = 0x00000001

    def _primary_guard(self) -> Optional[dict]:
        """渲染窗是否落在主显示器。返回拒绝信息 dict；不在主屏或 allow_primary 时返回 None。

        MonitorFromWindow(render_hwnd, MONITOR_DEFAULTTONEAREST) + GetMonitorInfo，
        Flags & MONITORINFOF_PRIMARY 命中即拒。硬拒绝，不等待、不降级绕过。
        """
        if self.allow_primary:
            return None
        hwnd = self.render_hwnd or self.main_hwnd
        if not hwnd:
            return None
        try:
            mon = win32api.MonitorFromWindow(hwnd, win32con.MONITOR_DEFAULTTONEAREST)
            info = win32api.GetMonitorInfo(mon)
        except Exception as e:
            # 探测失败不放行也不崩溃：记未知，交调用方按保守处理
            return {"refused": True, "reason": f"primary guard probe failed: {e}",
                    "monitor": None, "device": None, "flags": None}
        flags = info.get("Flags", 0)
        try:
            monitors = len(win32api.EnumDisplayMonitors())
        except Exception:
            monitors = -1
        if flags & self.MONITORINFOF_PRIMARY:
            return {"refused": True,
                    "reason": "refuse: target on primary display",
                    "monitor": hex(int(mon)),
                    "device": info.get("Device"),
                    "rc_monitor": list(info.get("Monitor", ())),
                    "flags": flags,
                    "monitors": monitors}
        return None

    def _visibility_diag(self, rect: Optional[Tuple[int, int, int, int]]) -> None:
        """诊断（不参与拒绝）：渲染窗 rect 与所有显示器 rc 求交，可见面积 < 窗口面积
        即记 partially-offscreen，单独一行警告入 clicks.log。"""
        if not rect:
            return
        l, t, r, b = rect
        area = max(0, r - l) * max(0, b - t)
        if area <= 0:
            return
        visible = 0
        try:
            for m in win32api.EnumDisplayMonitors():
                info = win32api.GetMonitorInfo(m[0])
                ml, mt, mr, mb = info["Monitor"]
                ix1, iy1 = max(l, ml), max(t, mt)
                ix2, iy2 = min(r, mr), min(b, mb)
                if ix2 > ix1 and iy2 > iy1:
                    visible += (ix2 - ix1) * (iy2 - iy1)
        except Exception:
            return
        if visible < area:
            self._log_raw(
                f"VISIBILITY warn render_rect={rect} visible_area={visible}/{area} "
                f"partially-offscreen")

    def render_to_screen(self, rx: float, ry: float) -> Optional[Tuple[int, int]]:
        """1280x720 渲染坐标 -> 屏幕物理像素。线性拉伸，无黑边假设。"""
        rect = self.render_rect()
        if rect is None:
            return None
        l, t, r, b = rect
        cw, ch = r - l, b - t
        if cw <= 0 or ch <= 0:
            return None
        sx = l + rx / RENDER_W * cw
        sy = t + ry / RENDER_H * ch
        return int(round(sx)), int(round(sy))

    def screen_to_render(self, sx: int, sy: int) -> Optional[Tuple[float, float]]:
        rect = self.render_rect()
        if rect is None:
            return None
        l, t, r, b = rect
        cw, ch = r - l, b - t
        rx = (sx - l) / cw * RENDER_W
        ry = (sy - t) / ch * RENDER_H
        return rx, ry

    # ------------------------------------------------------------ 前台/遮挡
    def _force_foreground(self, hwnd: int) -> None:
        """AttachThreadInput 绕过前台锁，再 SetForegroundWindow。每步独立容错，不阻塞。"""
        try:
            fg = win32gui.GetForegroundWindow()
            ftid = win32process.GetWindowThreadProcessId(fg)[0] if fg else 0
            tid = win32api.GetCurrentThreadId()
            attached = False
            try:
                if ftid:
                    attached = bool(user32.AttachThreadInput(tid, ftid, 1))
                if win32gui.IsIconic(hwnd):
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.BringWindowToTop(hwnd)
                try:
                    win32gui.SetForegroundWindow(hwnd)
                except Exception:
                    pass
                try:
                    win32gui.SetActiveWindow(hwnd)
                except Exception:
                    pass
            finally:
                if attached:
                    user32.AttachThreadInput(tid, ftid, 0)
        except Exception:
            pass

    def window_at(self, sx: int, sy: int) -> Optional[int]:
        try:
            return user32.WindowFromPoint(ctypes.wintypes.POINT(sx, sy))
        except Exception:
            return None

    def ensure_foreground(self) -> dict:
        """只记录前台句柄与矩形；【新规则】不做强切/不抢焦点（postmsg/adb 免前台）。"""
        info = {"fg_before": None, "fg_after": None, "rect": self._last_rect, "ok": False,
                "forced": False, "forced_attempted": False}
        try:
            info["fg_before"] = hex(win32gui.GetForegroundWindow())
            info["fg_before_title"] = win32gui.GetWindowText(win32gui.GetForegroundWindow())
        except Exception:
            pass
        try:
            info["fg_after"] = hex(win32gui.GetForegroundWindow())
            info["fg_after_title"] = win32gui.GetWindowText(win32gui.GetForegroundWindow())
        except Exception:
            pass
        rect = self.render_rect()
        info["rect"] = rect
        info["ok"] = rect is not None
        return info

    # ------------------------------------------------------------ 下发原语
    def _sendinput_click(self, sx: int, sy: int, hold_ms: int = 30) -> bool:
        win32api.SetCursorPos((sx, sy))
        time.sleep(0.02)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(hold_ms / 1000.0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        return True

    def _postmsg_click(self, rx_client: float, ry_client: float) -> bool:
        hwnd = self.render_hwnd
        if not hwnd:
            raise RuntimeError("no render hwnd")
        lparam = win32api.MAKELONG(int(rx_client), int(ry_client))
        # 先 MOUSEMOVE 让目标窗口跟踪光标，再 DOWN/UP（免前台，不抢焦点）
        win32gui.PostMessage(hwnd, win32con.WM_MOUSEMOVE, 0, lparam)
        win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
        time.sleep(0.03)
        win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)
        return True

    # ------------------------------------------------------------ 空闲探测
    @staticmethod
    def seconds_idle() -> float:
        """GetLastInputInfo：距上次键鼠输入秒数（GetTickCount 基准）。"""
        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]
        lii = LASTINPUTINFO()
        lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
        if not user32.GetLastInputInfo(ctypes.byref(lii)):
            return 1e9
        now = ctypes.windll.kernel32.GetTickCount()
        return max(0.0, (now - lii.dwTime) / 1000.0)

    def _adb_tap(self, rx: int, ry: int) -> Tuple[bool, str]:
        try:
            cp = subprocess.run(
                [self.adb_path, "-s", self.adb_serial, "shell", "input", "tap",
                 str(int(rx)), str(int(ry))],
                capture_output=True, timeout=15)
            if cp.returncode != 0:
                return False, cp.stderr.decode("utf-8", "ignore").strip() or "adb tap rc!=0"
            return True, ""
        except subprocess.TimeoutExpired:
            return False, "adb tap timeout"
        except FileNotFoundError:
            return False, "adb.exe not found"
        except Exception as e:
            return False, f"adb tap error {e}"

    # ------------------------------------------------------------ 主入口
    def click_render_xy(self, x: float, y: float, method: str = "auto",
                        semantic: str = "", seq: str = "click") -> dict:
        """点击渲染坐标 (x,y)。method: auto/mouse_sendinput/mouse_postmsg/adb。"""
        lock = self._lock_check(seq)
        if lock == "skip":
            return {"ok": False, "skipped": True, "method": "-",
                    "reason": "desktop lock busy; not counted"}
        t0 = time.perf_counter()
        result = {"ts": _iso(), "seq": seq, "semantic": semantic,
                  "render_xy": [round(float(x), 2), round(float(y), 2)],
                  "method": method, "ok": False, "skipped": False,
                  "elapsed_ms": None, "screen_xy": None, "errors": []}

        fg = self.ensure_foreground()
        result["fg_before"] = fg.get("fg_before")
        result["fg_after"] = fg.get("fg_after")
        result["fg_before_title"] = fg.get("fg_before_title")
        result["idle_s"] = round(self.seconds_idle(), 2)
        rect = self.render_rect()
        result["win_rect"] = list(rect) if rect else None
        self._visibility_diag(rect)

        screen = self.render_to_screen(x, y)
        result["screen_xy"] = screen
        if screen is None:
            result["errors"].append("render window rect unavailable (emulator closed?)")
            result["elapsed_ms"] = (time.perf_counter() - t0) * 1000
            self._log_click(result)
            return result

        # 遮挡检测（仅用于 sendinput 判定）
        under = self.window_at(*screen)
        result["under_point"] = hex(under) if under else None
        own = False
        if under and self.main_hwnd:
            root = user32.GetAncestor(under, 3)  # GA_ROOT
            own = root == self.main_hwnd or under in (self.render_hwnd, self.main_hwnd)
        result["own_window_under"] = bool(own)

        if not self.live:
            result["ok"] = True
            result["dry_run"] = True
            result["elapsed_ms"] = (time.perf_counter() - t0) * 1000
            self._log_click(result)
            return result

        # 主屏禁区守卫：渲染窗在主显示器 → 硬拒绝；postmsg/sendinput/adb 整条链都不许绕过
        guard = self._primary_guard()
        if guard:
            result["ok"] = False
            result["method"] = "-"
            result["errors"].append(guard["reason"])
            result["guard"] = guard
            self._log_raw(
                f"PRIMARY-GUARD refuse render_rect={rect} monitor={guard.get('monitor')} "
                f"device={guard.get('device')} monitors={guard.get('monitors')} "
                f"reason=target on primary display "
                f"action=connect secondary display | move LDPlayer inside (0,0)-(1920,1080) | "
                f"--allow-primary(not recommended)")
            result["elapsed_ms"] = round((time.perf_counter() - t0) * 1000, 2)
            self._log_click(result)
            return result

        # 通道尝试顺序（新规则：postmsg 为主，免前台不抢焦点；sendinput 仅空闲时；adb 兜底）
        order = [method] if method != "auto" else ["mouse_postmsg", "mouse_sendinput", "adb"]
        tried = []
        for m in order:
            tried.append(m)
            result["method"] = m
            try:
                if m == "mouse_sendinput":
                    idle = self.seconds_idle()
                    if idle < 5.0:
                        raise RuntimeError(f"user active (idle {idle:.1f}s<5s); sendinput skipped to avoid stealing focus")
                    if not own:
                        raise RuntimeError(f"occluded: top window at {screen} = {result['under_point']}, not LDPlayer")
                    self._sendinput_click(*screen)
                    result["ok"] = True
                elif m == "mouse_postmsg":
                    # 客户区坐标：渲染窗 client 左上为 0,0（免前台）
                    crect = win32gui.GetClientRect(self.render_hwnd)
                    scale_x = crect[2] / RENDER_W
                    scale_y = crect[3] / RENDER_H
                    self._postmsg_click(x * scale_x, y * scale_y)
                    result["ok"] = True
                elif m == "adb":
                    ok, err = self._adb_tap(int(round(x)), int(round(y)))
                    result["ok"] = ok
                    if not ok:
                        result["errors"].append(err)
                else:
                    result["errors"].append(f"unknown method {m}")
                    continue
            except Exception as e:
                result["ok"] = False
                result["errors"].append(f"{m} raised {e}")
            if result["ok"]:
                break
            result["method_tried"] = tried

        result["elapsed_ms"] = round((time.perf_counter() - t0) * 1000, 2)
        self._log_click(result)
        return result

    def click_tile(self, tile, calib=None, semantic: str = "", seq: str = "tile") -> dict:
        """tile: int（self.marks 序号，0 基）/ [gx,gy] / (gx,gy)。
        给 calib（geo.Calib）时 [gx,gy] -> px 走 tile_to_px。"""
        gx = gy = None
        if isinstance(tile, (list, tuple)) and len(tile) == 2:
            gx, gy = float(tile[0]), float(tile[1])
        elif isinstance(tile, int):
            if 0 <= tile < len(self.marks):
                m = self.marks[tile]
                gx, gy = m["tile"][0], m["tile"][1]
            else:
                res = {"ok": False, "method": "-", "errors": [f"tile index {tile} out of range"]}
                self._log_click({**res, "ts": _iso(), "seq": seq, "semantic": semantic})
                return res
        else:
            res = {"ok": False, "method": "-", "errors": [f"bad tile {tile!r}"]}
            self._log_click({**res, "ts": _iso(), "seq": seq, "semantic": semantic})
            return res
        if calib is not None:
            px, py = calib.tile_to_px(gx, gy)
        else:
            px, py = gx, gy
        return self.click_render_xy(px, py, semantic=semantic or f"tile({gx},{gy})", seq=seq)

    def tap_button(self, name: str, method: str = "auto", seq: str = "button") -> dict:
        if name not in ANCHORS:
            res = {"ok": False, "method": "-", "errors": [f"unknown button {name}"]}
            self._log_click({**res, "ts": _iso(), "seq": seq, "semantic": name})
            return res
        x, y = ANCHORS[name]
        return self.click_render_xy(x, y, method=method, semantic=f"button:{name}", seq=seq)

    def swipe_render(self, a: Tuple[float, float], b: Tuple[float, float],
                     dur_ms: int = 300, method: str = "auto", seq: str = "swipe") -> dict:
        lock = self._lock_check(seq)
        if lock == "skip":
            return {"ok": False, "skipped": True, "reason": "lock busy; not counted"}
        t0 = time.perf_counter()
        result = {"ts": _iso(), "seq": seq, "method": method,
                  "from": list(a), "to": list(b), "ok": False, "elapsed_ms": None}
        if not self.live:
            result["ok"] = True
            result["dry_run"] = True
            result["elapsed_ms"] = (time.perf_counter() - t0) * 1000
            self._log_click(result)
            return result
        # 主屏禁区守卫（swipe 同样硬拒绝，adb 也不许绕过）
        guard = self._primary_guard()
        if guard:
            result["ok"] = False
            result["method"] = "-"
            result["errors"] = [guard["reason"]]
            result["guard"] = guard
            self._log_raw(
                f"PRIMARY-GUARD refuse swipe render_rect={self._last_rect} monitor={guard.get('monitor')} "
                f"device={guard.get('device')} reason={guard['reason']}")
            result["elapsed_ms"] = round((time.perf_counter() - t0) * 1000, 2)
            self._log_click(result)
            return result
        fg = self.ensure_foreground()
        result["fg"] = fg.get("fg_after")
        try:
            if method in ("auto", "adb"):
                ok, err = self._adb_swipe(int(a[0]), int(a[1]), int(b[0]), int(b[1]), dur_ms)
                result["method"] = "adb"
                result["ok"] = ok
                if not ok:
                    result["errors"] = [err]
            else:
                # 鼠标拖拽（sendinput 序列）
                s1 = self.render_to_screen(*a)
                s2 = self.render_to_screen(*b)
                win32api.SetCursorPos(s1)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                steps = max(10, dur_ms // 20)
                for i in range(1, steps + 1):
                    ix = int(s1[0] + (s2[0] - s1[0]) * i / steps)
                    iy = int(s1[1] + (s2[1] - s1[1]) * i / steps)
                    win32api.SetCursorPos((ix, iy))
                    time.sleep(dur_ms / 1000.0 / steps)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                result["method"] = "mouse_sendinput"
                result["ok"] = True
        except Exception as e:
            result["errors"] = [f"swipe raised {e}"]
        result["elapsed_ms"] = round((time.perf_counter() - t0) * 1000, 2)
        self._log_click(result)
        return result

    def _adb_swipe(self, x1, y1, x2, y2, dur_ms) -> Tuple[bool, str]:
        try:
            cp = subprocess.run(
                [self.adb_path, "-s", self.adb_serial, "shell", "input", "swipe",
                 str(x1), str(y1), str(x2), str(y2), str(int(dur_ms))],
                capture_output=True, timeout=20)
            if cp.returncode != 0:
                return False, cp.stderr.decode("utf-8", "ignore").strip() or "swipe rc!=0"
            return True, ""
        except subprocess.TimeoutExpired:
            return False, "swipe timeout"
        except Exception as e:
            return False, f"swipe error {e}"

    # ------------------------------------------------------------ 状态/关闭
    def set_live(self, live: bool) -> None:
        self.live = bool(live)

    def adb_alive(self) -> bool:
        try:
            cp = subprocess.run([self.adb_path, "-s", self.adb_serial, "shell", "echo", "ok"],
                                capture_output=True, timeout=8)
            return cp.returncode == 0 and b"ok" in cp.stdout
        except Exception:
            return False

    def flush_rows_csv(self, path: str, fields: Sequence[str]) -> None:
        import csv
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            for r in self.rows:
                w.writerow(r)

    def close(self) -> None:
        self._closed = True
        # 无长驻子进程需要回收；写一份收尾日志
        self._log_raw("LdTouch.close() called; session ended")
