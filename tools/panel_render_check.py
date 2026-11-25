# -*- coding: utf-8 -*-
"""PANEL 离屏渲染自检：不开可见窗口，不碰桌面，只验证字体与排版是否叠字。

用法：python tools\panel_render_check.py [--out out\overlay\panel_offscreen.png]
判据（脚本自动打印）：
  - msyh.ttc 是否加载成功（font_ready）
  - 面板右上标签区、状态行、步骤行三处像素是否仍有"双层文字"残留（按行黑度分布粗判）
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

W, H = 997, 561          # 默认=实机窗口化客户区；全屏请传 --w 1920 --h 1080


def _load_candidates(root):
    p = os.path.join(root, "out", "overlay", "layout_candidates.json")
    try:
        with open(p, encoding="utf-8") as f:
            raw = json.load(f)
        rows = raw.get("candidates") if isinstance(raw, dict) else raw
        if rows:
            return rows[:8]
    except Exception:
        pass
    # 兜底：合成 8 条，只为看字
    return [
        {"id": f"c{i}", "label": ["防空火箭", "箭塔", "加农炮", "法师塔",
                                  "地狱之塔", "X连弩", "特斯拉电磁塔", "城墙"][i],
         "type": "x", "bbox": [40 + i * 60, 40 + i * 40, 80 + i * 60, 80 + i * 40],
         "confidence": 0.9 - i * 0.08}
        for i in range(8)
    ]


class _State:
    root = "."
    page = "layout"
    live = False
    study_png = None
    study_brief = "赛前简报：对面防空偏左，蛮王前顶。"
    study_info = {"defense_counts": {"airdef": 4, "archer-tower": 6}}
    candidates = []
    candidates_png = None
    quad_px = None


class _Ctx:
    """最小上下文桩：只提供 pages 会调到的接口。"""

    font_ready = True

    def __init__(self, root):
        self.root = root
        self.geo = None
        self.textures = {}

    def log(self, msg):
        print(f"[ctx] {msg}")

    def set_page(self, page):
        self.rt_page = page

    def mouse(self):
        return (-1.0, -1.0, False, False, 0.0)

    def texture(self, *a, **k):
        return 0

    def freeze_layout(self, *a, **k):
        return {"ok": False, "message": "offscreen-check: 不落盘"}

    def panel_rect(self):
        return (W - 420.0, 0.0, 420.0, H)

    def dpi_scale(self):
        return 1.0


def main():
    global W, H
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--out", default=None)
    ap.add_argument("--w", type=int, default=997, help="离屏画布宽（全屏用 1920）")
    ap.add_argument("--h", type=int, default=561, help="离屏画布高（全屏用 1080）")
    ap.add_argument("--page", default="research",
                    help="research/layout/collect/setting(=settings)")
    ap.add_argument("--engine", default="local", help="local/llm（研究页的引擎模式）")
    ap.add_argument("--demo", default="normal", choices=["normal", "capture", "conflict"],
                    help="设置页演示态：normal/capture/conflict")
    ap.add_argument("--layout", default=None,
                    help="可选 layout.json；注入 state.layout，供研究页推演行/弱点行离线出图")
    a = ap.parse_args()
    # 设置页别名：settings -> setting
    a.page = {"settings": "setting"}.get(a.page, a.page)
    W, H = int(a.w), int(a.h)
    out = a.out or os.path.join(a.root, "out", "overlay", "panel_offscreen.png")

    import glfw
    from imgui_bundle import imgui
    from imgui_bundle.python_backends.glfw_backend import GlfwRenderer
    import OpenGL.GL as gl
    from PIL import Image

    st = _State()
    st.root = a.root
    st.page = a.page
    st.candidates = _load_candidates(a.root)
    st.layout = None
    if a.layout:
        try:
            with open(a.layout, encoding="utf-8") as f:
                st.layout = json.load(f)
            print(f"layout loaded: {a.layout} buildings={len(st.layout.get('buildings') or [])}")
        except Exception as e:  # noqa: BLE001
            print(f"layout load failed: {e!r}")
    from clashlab.overlay import tactics
    tactics.SEL["engine"] = a.engine
    ctx = _Ctx(a.root)

    if not glfw.init():
        raise SystemExit("glfw init failed")
    glfw.window_hint(glfw.VISIBLE, glfw.FALSE)          # 关键：不可见，不占桌面
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 2)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    win = glfw.create_window(W, H, "panel-offscreen-check", None, None)
    glfw.make_context_current(win)

    imgui.create_context()
    io = imgui.get_io()
    io.set_ini_filename("")
    font_ok = False
    try:
        io.fonts.add_font_from_file_ttf(r"C:\Windows\Fonts\msyh.ttc", 18.0)
        font_ok = True
    except Exception as e:
        io.fonts.add_font_default()
        print(f"font load failed: {e!r}")
    ctx.font_ready = font_ok
    renderer = GlfwRenderer(win)

    from clashlab.overlay import pages
    # ---- 设置页演示态预置（capture/conflict 仅离屏出图用） ----
    if a.page == "setting":
        from clashlab.overlay import keys as _kb
        _kb.load(a.root)
        pages._SESSION["keys_loaded_root"] = a.root
        pages._SESSION["keys_capture"] = None
        pages._SESSION["keys_msg"] = None
        if a.demo == "capture":
            pages._SESSION["keys_capture"] = "capture"
        elif a.demo == "conflict":
            pages._SESSION["keys_capture"] = "capture"
            pages._SESSION["keys_msg"] = ("red", "已被 切换面板 占用")
    imgui.new_frame()
    io.display_size = imgui.ImVec2(float(W), float(H))

    # ---- 数值探针（先于 pages 绘制，排除 pages 状态干扰）----
    _dl = imgui.get_foreground_draw_list()
    _px0, _py0 = 20.0, H - 64.0
    _dl.add_rect_filled(imgui.ImVec2(_px0, _py0),
                        imgui.ImVec2(_px0 + 160.0, _py0 + 30.0),
                        imgui.color_convert_float4_to_u32(imgui.ImVec4(0, 0, 0, 1.0)), 4.0)
    _dl.add_text(imgui.ImVec2(_px0 + 10.0, _py0 + 7.0),
                 imgui.color_convert_float4_to_u32(imgui.ImVec4(1, 1, 1, 1.0)),
                 "PROBE 123")

    pages.draw_panel(ctx, st)

    gl.glViewport(0, 0, W, H)
    gl.glClearColor(0.08, 0.12, 0.10, 1.0)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT)
    imgui.render()
    renderer.render(imgui.get_draw_data())
    gl.glFinish()

    buf = gl.glReadPixels(0, 0, W, H, gl.GL_RGB, gl.GL_UNSIGNED_BYTE)
    img = Image.frombytes("RGB", (W, H), buf)
    img = img.transpose(Image.FLIP_TOP_BOTTOM)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.save(out)

    px = img.load()

    def band_luma(x0, y0, x1, y1):
        """屏幕坐标带（翻转后读回）：返回 max/mean/非零像素占比。"""
        ys = sorted((H - y1, H - y0))
        vals, nz = [], 0
        for y in range(max(0, int(ys[0])), min(H, int(ys[1]))):
            for x in range(max(0, int(x0)), min(W, int(x1))):
                r, g, b = px[x, y]
                lum = 0.299 * r + 0.587 * g + 0.114 * b
                vals.append(lum)
                if lum > 24:
                    nz += 1
        if not vals:
            return 0.0, 0.0, 0.0
        return max(vals), sum(vals) / len(vals), nz / len(vals)

    def ink_rows(y0, y1, x0, x1):
        segs, cur = [], 0
        for y in range(int(y0), int(y1)):
            n = sum(1 for x in range(int(x0), int(x1)) if sum(px[x, y]) > 120)
            if n > 3:
                cur += 1
            else:
                if cur:
                    segs.append(cur)
                cur = 0
        if cur:
            segs.append(cur)
        return segs

    print(f"font_ready={font_ok}  out={out}")
    # ---- 布局栈复算（与 pages._draw_layout 同一公式）----
    pw = min(420.0, W * 0.45)
    px0 = W - pw
    avail = (H - 44.0) - 112.0
    fixed = 26.0 + 28.0 + 26.0 + 24.0
    list_h = min(120.0, max(48.0, avail - fixed - 16.0 - 420.0))
    canvas_h = min(420.0, max(120.0, avail - fixed - 16.0 - list_h))
    y_filter = 112.0 + canvas_h + 8.0
    y_list = y_filter + 26.0 + 8.0
    y_freeze = y_list + list_h + 8.0
    print(f"[STACK] canvas_h={canvas_h:.0f} list_h={list_h:.0f} "
          f"y_filter={y_filter:.0f} y_list={y_list:.0f} y_freeze={y_freeze:.0f}")
    # 探针块（屏幕 y=H-64..H-34，面板外 x=20）
    pm, pa, pnz = band_luma(20, H - 64, 180, H - 34)
    print(f"[PROBE] white-on-black max={pm:.1f} mean={pa:.1f} nonzero={pnz:.3f}  "
          f"(判据 max>=200)")
    # 同图四区域对照（layout 页：筛选行 / 冻结按钮 / 候选首行）
    for name, (rx0, ry0, rx1, ry1) in {
        "筛选行(候选筛选)": (px0 + 8, y_filter, W - 10, y_filter + 26),
        "冻结按钮行": (px0 + 8, y_freeze, px0 + 170, y_freeze + 28),
        "候选列表首行": (px0 + 8, y_list + 2, W - 10, y_list + 28),
    }.items():
        lm, la, ln = band_luma(rx0, ry0, rx1, ry1)
        print(f"[{name}] max={lm:.1f} mean={la:.1f} nonzero={ln:.3f}  (判据 max>=200)")
    # 各区域亮度（屏幕坐标带）
    for name, (rx0, ry0, rx1, ry1) in {
        "tabs标题行": (W - 406, 10, W - 10, 40),
        "status状态行": (W - 406, 46, W - 10, 72),
        "画布提示行": (px0 + 8, 116, W - 10, 150),
        "底部状态栏": (W - 406, H - 40, W - 10, H - 8),
    }.items():
        lm, la, ln = band_luma(rx0, ry0, rx1, ry1)
        print(f"[{name}] max={lm:.1f} mean={la:.1f} nonzero={ln:.3f}")
    print(f"tabs band  y8-34  segs={ink_rows(8, 34, W - 420, W)}")
    print(f"status band y34-56 segs={ink_rows(34, 56, W - 420, W)}")

    renderer.shutdown()
    glfw.terminate()


if __name__ == "__main__":
    main()
