# -*- coding: utf-8 -*-
"""逐帧性能打点（默认关闭；环境变量 CLASH_PERF=1 开启）。

设计红线（与任务书一致）：
- 未开启（CLASH_PERF 未置 1）时，本模块所有公共接口为薄直通 / no-op：
  渲染路径不增一次 GL 调用，不改 glfw.swap_interval，不改 pacing 参数，
  绘制结果与原版逐帧一致。
- 开启时：逐帧落 JSONL（默认 out/overlay/perf_raw.jsonl，可用 CLASH_PERF_OUT
  指定绝对/相对路径覆盖），每 10s 向 stdout 打一个窗口汇总，退出补末窗。

分段口径（全部 wall-clock，单位 ms，time.perf_counter）：
- build_ms   : imgui.new_frame() -> 本帧标注绘制调用结束（ImGui 构建 + draw.* 调用）
- submit_ms  : renderer.process_inputs() + imgui.render() + renderer.render(draw_data)（GL 提交）
- swap_ms    : glfw.swap_buffers(window) 实际阻塞（vsync/DWM 呈现）——与 pacing 分开
- pace_ms    : 显式 60fps pacing 的 time.sleep(sl) 时长——与 swap_ms 分开，避免混算
- gwr_n/gwr_ms : 本帧 win32gui.GetWindowRect 调用次数 / 累计耗时（仅开启时装 hook）
- swp_n       : 本帧 win32gui.SetWindowPos 调用次数（仅开启时装 hook）
- vtx/cmd     : imgui draw data 顶点总数 / draw command 总数
- mode        : 当前模式 HUD/PANEL；win_rect : 覆盖层窗口 rect [l,t,r,b]；
  target : 目标渲染面 (tx,ty,tw,th)，供 S2 看 rect sync
"""
from __future__ import annotations

import json
import os
import time

# ---- 门控：默认关闭。CLASH_PERF=1 / true / on / yes 开启（大小写不敏感）----
_ENABLED = os.environ.get("CLASH_PERF", "").strip().lower() in ("1", "true", "on", "yes")


def _pct(vals, p: float) -> float:
    """线性插值百分位（纯标准库，不依赖 numpy）。p in [0,100]。"""
    if not vals:
        return 0.0
    s = sorted(vals)
    k = (len(s) - 1) * p / 100.0
    f = int(k)
    c = min(f + 1, len(s) - 1)
    if f == c:
        return float(s[f])
    return float(s[f] + (s[c] - s[f]) * (k - f))


class _Recorder:
    """开启时的真实记录器；关闭时模块层不实例化本类。"""

    WINDOW_S = 10.0  # 汇总窗口长度（秒）

    def __init__(self) -> None:
        self.out_path = None
        self._fh = None
        self._run_t0 = None
        self._win_start = None
        self._rows: list[dict] = []
        # 每帧累加器（frame_begin 复位）
        self.frame_n = 0
        self.mode = "HUD"
        self.build_ms = 0.0
        self.submit_ms = 0.0
        self.swap_ms = 0.0
        self.pace_ms = 0.0
        self.gwr_n = 0
        self.gwr_ms = 0.0
        self.swp_n = 0
        self.vtx = 0
        self.cmd = 0
        self._tb = 0.0
        self._ts = 0.0
        # hook 原件（attach 时保存，end_run 还原）
        self._orig_gwr = None
        self._orig_swp = None

    # ---------------------------------------------------------- 生命周期
    def begin(self, root: str) -> None:
        """打开 JSONL；CLASH_PERF_OUT 可覆盖输出路径。"""
        override = os.environ.get("CLASH_PERF_OUT", "").strip()
        if override:
            self.out_path = override if os.path.isabs(override) else os.path.join(root, override)
        else:
            self.out_path = os.path.join(root, "out", "overlay", "perf_raw.jsonl")
        os.makedirs(os.path.dirname(self.out_path), exist_ok=True)
        self._fh = open(self.out_path, "w", encoding="utf-8")
        self._run_t0 = time.perf_counter()
        self._win_start = self._run_t0
        print(f"[PERF] CLASH_PERF=1 enabled; raw -> {self.out_path}")

    def attach_hooks(self) -> None:
        """给 win32gui.GetWindowRect / SetWindowPos 装计数 hook；仅开启时调用。"""
        import win32gui

        self._orig_gwr = win32gui.GetWindowRect
        self._orig_swp = win32gui.SetWindowPos
        rec = self

        def _gwr(hwnd):
            t0 = time.perf_counter()
            v = rec._orig_gwr(hwnd)
            rec.gwr_n += 1
            rec.gwr_ms += (time.perf_counter() - t0) * 1000.0
            return v

        def _swp(hwnd, after, x, y, cx, cy, flags):
            rec.swp_n += 1
            return rec._orig_swp(hwnd, after, x, y, cx, cy, flags)

        win32gui.GetWindowRect = _gwr
        win32gui.SetWindowPos = _swp

    def _detach_hooks(self) -> None:
        import win32gui

        if self._orig_gwr is not None:
            win32gui.GetWindowRect = self._orig_gwr
            self._orig_gwr = None
        if self._orig_swp is not None:
            win32gui.SetWindowPos = self._orig_swp
            self._orig_swp = None

    # ---------------------------------------------------------- 帧分段
    def frame_begin(self, frame_n: int, mode: str) -> None:
        self.frame_n = frame_n
        self.mode = mode
        self.build_ms = self.submit_ms = self.swap_ms = self.pace_ms = 0.0
        self.gwr_n = 0
        self.gwr_ms = 0.0
        self.swp_n = 0
        self.vtx = 0
        self.cmd = 0
        self._tb = time.perf_counter()
        self._ts = 0.0

    def build_begin(self) -> None:
        self._tb = time.perf_counter()

    def build_end(self) -> None:
        self.build_ms = (time.perf_counter() - self._tb) * 1000.0

    def submit_begin(self) -> None:
        self._ts = time.perf_counter()

    def submit_end(self) -> None:
        self.submit_ms = (time.perf_counter() - self._ts) * 1000.0

    def swap_buffers(self, window, glfw_mod) -> None:
        t0 = time.perf_counter()
        glfw_mod.swap_buffers(window)
        self.swap_ms = (time.perf_counter() - t0) * 1000.0

    def pace_sleep(self, sl: float) -> None:
        """替代 time.sleep(sl)：只在 sl>0 时睡，记录真实睡眠时长。"""
        if sl > 0:
            t0 = time.perf_counter()
            time.sleep(sl)
            self.pace_ms = (time.perf_counter() - t0) * 1000.0

    def collect_draw_data(self, imgui_mod) -> None:
        """开启态才在内部取 get_draw_data；关闭态调用方不传 draw data。"""
        dd = None
        try:
            dd = imgui_mod.get_draw_data()
        except Exception:
            dd = None
        if dd is None:
            return
        try:
            self.vtx = int(getattr(dd, "total_vtx_count", 0) or 0)
        except Exception:
            self.vtx = 0
        try:
            n = 0
            for dl in dd.cmd_lists:
                n += int(dl.cmd_buffer.size())
            self.cmd = n
        except Exception:
            self.cmd = 0

    # ---------------------------------------------------------- 落盘 / 汇总
    def frame_end(self, now_t: float, dt_ms: float, mode: str,
                  win_rect=None, target=None) -> None:
        wall_s = now_t - self._run_t0
        row = {
            "frame": self.frame_n,
            "wall_s": round(wall_s, 4),
            "dt_ms": round(dt_ms, 4),
            "build_ms": round(self.build_ms, 4),
            "submit_ms": round(self.submit_ms, 4),
            "swap_ms": round(self.swap_ms, 4),
            "pace_ms": round(self.pace_ms, 4),
            "gwr_n": self.gwr_n,
            "gwr_ms": round(self.gwr_ms, 4),
            "swp_n": self.swp_n,
            "vtx": self.vtx,
            "cmd": self.cmd,
            "mode": mode,
            "win_rect": list(win_rect) if win_rect else None,
            "target": list(target) if target else None,
        }
        self._rows.append(row)
        self._fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        self._fh.flush()
        if wall_s - self._win_start >= self.WINDOW_S:
            self._summarize(self._rows, final=False)
            self._rows = []
            self._win_start = wall_s

    def _summarize(self, rows: list[dict], final: bool) -> None:
        if not rows:
            return
        dts = [r["dt_ms"] for r in rows]
        builds = [r["build_ms"] for r in rows]
        subs = [r["submit_ms"] for r in rows]
        swps = [r["swap_ms"] for r in rows]
        paces = [r["pace_ms"] for r in rows]
        gwr_ms = [r["gwr_ms"] for r in rows]
        t0 = rows[0]["wall_s"]
        t1 = rows[-1]["wall_s"]
        p50 = _pct(dts, 50)
        fps_eq = 1000.0 / p50 if p50 > 0 else 0.0
        fps_mean = 1000.0 / (sum(dts) / len(dts)) if dts else 0.0
        gwr_calls = sum(r["gwr_n"] for r in rows)
        swp_calls = sum(r["swp_n"] for r in rows)
        tag = "FINAL" if final else "window"
        print(f"[PERF] {tag} {t0:.1f}s->{t1:.1f}s frames={len(rows)}")
        print(f"[PERF]   dt_ms    p50={_pct(dts,50):.3f} p95={_pct(dts,95):.3f} "
              f"max={max(dts):.3f}  fps_eq@p50={fps_eq:.2f} fps_mean={fps_mean:.2f}")
        print(f"[PERF]   build_ms  p50={_pct(builds,50):.3f} p95={_pct(builds,95):.3f}")
        print(f"[PERF]   submit_ms p50={_pct(subs,50):.3f} p95={_pct(subs,95):.3f}")
        print(f"[PERF]   swap_ms   p50={_pct(swps,50):.3f} p95={_pct(swps,95):.3f} "
              f"(vsync/DWM 实际阻塞，与 pacing 分开)")
        print(f"[PERF]   pace_ms   p50={_pct(paces,50):.3f} p95={_pct(paces,95):.3f} "
              f"(显式 60fps pacing sleep)")
        print(f"[PERF]   gwr calls={gwr_calls} total_ms={sum(gwr_ms):.3f} "
              f"p95={_pct(gwr_ms,95):.4f} | SetWindowPos calls={swp_calls}")

    def end_run(self) -> None:
        self._summarize(self._rows, final=True)
        self._rows = []
        self._detach_hooks()
        try:
            if self._fh is not None:
                self._fh.close()
        except Exception:
            pass
        self._fh = None


# ---------------------------------------------------------- 模块层门面（关闭即直通）
_rec = _Recorder() if _ENABLED else None


def begin(root: str) -> None:
    if _rec is not None:
        _rec.begin(root)


def attach_hooks() -> None:
    if _rec is not None:
        _rec.attach_hooks()


def frame_begin(frame_n: int, mode: str) -> None:
    if _rec is not None:
        _rec.frame_begin(frame_n, mode)


def build_begin() -> None:
    if _rec is not None:
        _rec.build_begin()


def build_end() -> None:
    if _rec is not None:
        _rec.build_end()


def submit_begin() -> None:
    if _rec is not None:
        _rec.submit_begin()


def submit_end() -> None:
    if _rec is not None:
        _rec.submit_end()


def swap_buffers(window, glfw_mod) -> None:
    """开启：计时包裹 swap；关闭：原样直通 glfw_mod.swap_buffers。"""
    if _rec is not None:
        _rec.swap_buffers(window, glfw_mod)
    else:
        glfw_mod.swap_buffers(window)


def pace_sleep(sl: float) -> None:
    """开启：计时包裹 sleep；关闭：与原版 `if sl > 0: time.sleep(sl)` 等价直通。"""
    if _rec is not None:
        _rec.pace_sleep(sl)
    elif sl > 0:
        time.sleep(sl)


def collect_draw_data(imgui_mod) -> None:
    if _rec is not None:
        _rec.collect_draw_data(imgui_mod)


def frame_end(now_t: float, dt_ms: float, mode: str, win_rect=None, target=None) -> None:
    if _rec is not None:
        _rec.frame_end(now_t, dt_ms, mode, win_rect=win_rect, target=target)


def end_run() -> None:
    if _rec is not None:
        _rec.end_run()
