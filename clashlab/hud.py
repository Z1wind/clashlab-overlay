# -*- coding: utf-8 -*-
"""HUD：一个点击穿透的实时绘制层 + 一个独立的小窗策略面板。

全部基于 Tk，不引入额外 GUI 依赖；窗口样式用 Win32 扩展风格设置，
使 overlay 不抢焦点、不接收鼠标，面板可选交互。

已弃用：线性公式（hud_linear：cx/cy/kx/ky 四边线性插值），实测错位
32.19px ≈ 2.6 格（见 out/audit/mustfix_report.md P0-01 数值证明）。
所有网格/撒兵点坐标统一走 clashlab.geo.Calib 的 tile_to_px 单应映射。
"""
import ctypes
import tkinter as tk

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOOLWINDOW = 0x00000080

TRANSPARENT_KEY = "#010203"

YELLOW = "#f0c452"
ORANGE = "#e27a38"
GREEN = "#60c882"
BLUE = "#78bee6"
INK = "#eef0f2"
GREY = "#969ca0"


def _top_hwnd(win):
    hwnd = win.winfo_id()
    parent = ctypes.windll.user32.GetParent(hwnd)
    return parent or hwnd


def make_click_through(win):
    hwnd = _top_hwnd(win)
    ex = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    ctypes.windll.user32.SetWindowLongW(
        hwnd, GWL_EXSTYLE,
        ex | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW)
    return hwnd


class Hud:
    def __init__(self, width=1280, height=720, panel_only=False):
        self.root = tk.Tk()
        self.root.withdraw()
        self.width = width
        self.height = height
        self.panel_only = panel_only
        self.paused = False

        if not panel_only:
            self.overlay = tk.Toplevel(self.root)
            self.overlay.overrideredirect(True)
            self.overlay.geometry(f"{width}x{height}+40+40")
            self.overlay.configure(bg=TRANSPARENT_KEY)
            try:
                self.overlay.attributes("-transparentcolor", TRANSPARENT_KEY)
            except Exception:
                pass
            self.overlay.attributes("-topmost", True)
            self.canvas = tk.Canvas(self.overlay, bg=TRANSPARENT_KEY, highlightthickness=0)
            self.canvas.pack(fill="both", expand=True)
            self._hwnd_overlay = make_click_through(self.overlay)

        self.panel = tk.Toplevel(self.root)
        self.panel.overrideredirect(True)
        pw, ph = 340, 470
        self.panel.geometry(f"{pw}x{ph}+{width - pw - 60}+70")
        self.panel.configure(bg="#101418")
        self.panel.attributes("-topmost", True)
        self.panel.bind("<space>", self._toggle_pause)
        self._hwnd_panel = make_click_through(self.panel)

        self._build_panel(pw, ph)
        self.state = {"info": {}, "plan": None}

    def _build_panel(self, pw, ph):
        bd = "#4c565e"
        tk.Frame(self.panel, bg=bd).place(x=8, y=8, width=pw - 16, height=ph - 16)
        tk.Frame(self.panel, bg="#0c1013").place(x=9, y=9, width=pw - 18, height=ph - 18)
        tk.Label(self.panel, text="作战计划", bg="#0c1013", fg=INK,
                 font=("Microsoft YaHei", 13, "bold")).place(x=22, y=20)
        self.lbl_state = tk.Label(self.panel, text="等待画面", bg="#0c1013", fg=GREY,
                                  font=("Microsoft YaHei", 9), anchor="w", justify="left")
        self.lbl_state.place(x=22, y=52, width=pw - 44, height=54)

        self.steps_box = tk.Text(self.panel, bg="#0c1013", fg=INK, bd=0,
                                 highlightthickness=0, font=("Microsoft YaHei", 9),
                                 width=30, height=8, wrap="word")
        self.steps_box.place(x=22, y=112, width=pw - 44, height=170)
        self.steps_box.configure(state="disabled")

        self.lbl_conf = tk.Label(self.panel, text="预测得分 0.00", bg="#0c1013", fg="#a0d2af",
                                 font=("Microsoft YaHei", 9), anchor="w")
        self.lbl_conf.place(x=22, y=294, width=pw - 44)
        self.bar = tk.Canvas(self.panel, bg="#0c1013", highlightthickness=0)
        self.bar.place(x=22, y=316, width=pw - 44, height=10)
        self.bar.create_rectangle(0, 0, pw - 44, 10, fill="#262e33", outline="")
        self.bar_item = self.bar.create_rectangle(0, 0, 0, 10, fill=GREEN, outline="")

        tk.Label(self.panel, text="解说", bg="#0c1013", fg="#8296a2",
                 font=("Microsoft YaHei", 8)).place(x=22, y=338)
        self.lbl_note = tk.Label(self.panel, text="—", bg="#0c1013", fg="#cdd4da",
                                 font=("Microsoft YaHei", 9), anchor="nw", justify="left", wraplength=pw - 54)
        self.lbl_note.place(x=22, y=358, width=pw - 44, height=54)

        self.btn = tk.Label(self.panel, text="SPACE  接管", bg="#582222", fg="#eec8c8",
                            font=("Microsoft YaHei", 9, "bold"))
        self.btn.place(x=22, y=ph - 56, width=pw - 44, height=32)
        self.btn.bind("<Button-1>", lambda e: self._toggle_pause())

    def _toggle_pause(self, _e=None):
        self.paused = not self.paused
        self.btn.configure(text="已暂停  按 SPACE 继续" if self.paused else "SPACE  接管",
                           bg="#3a4a2a" if self.paused else "#582222")

    # ---------- 绘制 ----------
    def update_state(self, info, plan=None):
        self.state = {"info": info, "plan": plan}
        if not self.panel_only:
            self._draw_overlay(info, plan)
        self._draw_panel(info, plan)

    def _draw_overlay(self, info, plan):
        c = self.canvas
        c.delete("all")
        quad = info.get("boundary", {}).get("quad")
        if not quad:
            return
        c.create_polygon([coord for p in quad for coord in p], outline="#f0f0f0", fill="")

        # P0-01：网格与撒兵点全部走 geo.Calib 单应矩阵，不再做四边线性插值。
        from .geo import Calib
        calib = Calib.from_quad(quad, n=44)

        for g in range(0, 45, 4):
            # 纵向线：(g,0) -> (g,44)
            x0, y0 = calib.tile_to_px(g, 0)
            x1, y1 = calib.tile_to_px(g, 44)
            c.create_line(x0, y0, x1, y1, fill="#ffffff", width=1, stipple="gray50")
            # 横向线：(0,g) -> (44,g)
            x0, y0 = calib.tile_to_px(0, g)
            x1, y1 = calib.tile_to_px(44, g)
            c.create_line(x0, y0, x1, y1, fill="#ffffff", width=1, stipple="gray50")

        if plan:
            # 箭头指向菱形几何中心（仅作视觉锚点，不参与格坐标换算）
            cx = sum(p[0] for p in quad) / 4
            cy = sum(p[1] for p in quad) / 4
            for e in plan["entry"]:
                gx, gy = e["tile"]
                px, py = calib.tile_to_px(gx, gy)
                c.create_oval(px - 15, py - 15, px + 15, py + 15, fill=GREEN, outline="#12351f")
                c.create_text(px, py, text=str(e["step"]), fill="#0d2415",
                              font=("Microsoft YaHei", 10, "bold"))
                c.create_line(px, py, cx, cy, fill=YELLOW, width=2, arrow="last")

    def _draw_panel(self, info, plan):
        b = info.get("boundary", {})
        self.lbl_state.configure(
            text=f"状态  {info.get('state', '-')}\n"
                 f"标定  {b.get('source') or '无'}    红区 {info.get('red_ratio', 0):.2f}\n"
                 f"重投影误差  {info.get('reproj') if info.get('reproj') is not None else '-'} px")
        self.steps_box.configure(state="normal")
        self.steps_box.delete("1.0", "end")
        if plan:
            for i, e in enumerate(plan["entry"]):
                mark = "▶" if i == 0 else " "
                self.steps_box.insert("end", f"{mark} {e['step']}. ({e['tile'][0]},{e['tile'][1]}) "
                                             f"雷龙×{e['count']}   {e['score']:.2f}\n")
        else:
            self.steps_box.insert("end", "未生成计划：\n缺少建筑清单或未识别到战场")
        self.steps_box.configure(state="disabled")

        conf = plan.get("predicted", 0.0) if plan else 0.0
        self.lbl_conf.configure(text=f"预测得分 {conf:.2f}")
        w = (self.panel.winfo_width() or 340) - 44
        self.bar.coords(self.bar_item, 0, 0, w * min(conf, 1.0), 10)
        self.lbl_note.configure(text=info.get("note") or "—")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    Hud().run()
