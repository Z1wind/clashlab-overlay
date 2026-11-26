# -*- coding: utf-8 -*-
"""给 HUD 绘制加光晕/胶囊/角括号，提升观感（不改坐标口径）。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "overlay", "draw.py")
t = open(p, encoding="utf-8").read()

helpers = '''
# ---------------------------------------------------------------- 视觉增强
# 只加「画得好看」的装饰层：光晕/胶囊/角括号，全部走同一 tile->px 口径，不改坐标。

def _rgba(col, a):
    return (col[0], col[1], col[2], a)


def _glow(dl, x, y, r, col, rings=3, base_alpha=0.20):
    """同心圆光晕：外圈更淡，做出发光感（纯装饰，不影响命中）。"""
    for i in range(rings, 0, -1):
        rr = r + i * 3.2
        dl.add_circle_filled(imgui_pt(x, y), rr, _col(_rgba(col, base_alpha / i)), 40)


def _chip(dl, x, y, text, fg, bg=None, pad_x=5.0, pad_y=2.0):
    """小胶囊底 + 描边文字：HUD 文案在草地/雪地上都清晰。"""
    from imgui_bundle import imgui
    tw, th = imgui.calc_text_size(str(text))
    bgc = bg or theme.HUD_CAP
    dl.add_rect_filled(imgui_pt(x - pad_x, y - pad_y),
                       imgui_pt(x + tw + pad_x, y + th + pad_y),
                       _col(bgc), rounding=5.0)
    dl.add_rect(imgui_pt(x - pad_x, y - pad_y),
                imgui_pt(x + tw + pad_x, y + th + pad_y),
                _col(_rgba(fg, 0.28)), rounding=5.0, thickness=1.0)
    _text_outline(dl, x, y, str(text), fg)


def _brackets(dl, x0, y0, x1, y1, col, size=7.0, thickness=2.4):
    """四角括号：比整圈方框更轻、更有「战术标记」感。"""
    c = _col(col)
    for (cx, cy, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1),
                             (x0, y1, 1, -1), (x1, y1, -1, -1)):
        dl.add_line(imgui_pt(cx, cy), imgui_pt(cx + sx * size, cy), c, thickness)
        dl.add_line(imgui_pt(cx, cy), imgui_pt(cx, cy + sy * size), c, thickness)


'''

anchor = "def draw_marks(dl, calib, marks: dict, win_w: float, win_h: float) -> None:"
if "_glow(dl" in t:
    print("already patched")
else:
    t = t.replace(anchor, helpers + anchor, 1)
    old_marks = '''        role = m.get("role")
        seq = m.get("seq")
        if role == "target":
            dl.add_circle(imgui_pt(x, y), 10.0, _col(ORANGE), 0, 2.0)
            if seq is not None:
                _text_outline(dl, x + 13, y - 7, str(seq), INK)
        else:  # avoid / 其它
            dl.add_circle(imgui_pt(x, y), 6.0, _col(BLUE), 0, 1.5)
        label = m.get("label")
        if label:
            _text_outline(dl, x + 10, y + 8, str(label), GREY)'''
    new_marks = '''        role = m.get("role")
        seq = m.get("seq")
        if role == "target":
            # 目标：暖橙光晕 + 双环 + 中心亮点 + 编号胶囊
            _glow(dl, x, y, 9.0, ORANGE, rings=3, base_alpha=0.30)
            dl.add_circle_filled(imgui_pt(x, y), 3.0, _col(_rgba(ORANGE, 0.95)), 24)
            dl.add_circle(imgui_pt(x, y), 10.0, _col(ORANGE), 40, 2.4)
            dl.add_circle(imgui_pt(x, y), 14.0, _col(_rgba(ORANGE, 0.45)), 40, 1.2)
            if seq is not None:
                _chip(dl, x + 17, y - 9, str(seq), INK, bg=_rgba(ORANGE, 0.18))
        else:  # avoid / 其它：冷灰蓝小点 + 柔和光晕
            _glow(dl, x, y, 5.5, BLUE, rings=2, base_alpha=0.22)
            dl.add_circle_filled(imgui_pt(x, y), 2.5, _col(_rgba(BLUE, 0.95)), 20)
            dl.add_circle(imgui_pt(x, y), 6.0, _col(_rgba(BLUE, 0.85)), 28, 1.6)
        label = m.get("label")
        if label:
            _chip(dl, x + 12, y + 9, str(label), GREY)'''
    if old_marks in t:
        t = t.replace(old_marks, new_marks, 1)
    else:
        print("marks anchor miss")
    old_sel = '''        if sel:
            hw = 1.6 * tile_x * sx
            hh = 1.1 * tile_y * sy
            dl.add_rect_filled(imgui_pt(x - hw, y - hh), imgui_pt(x + hw, y + hh),
                               col=_col((col[0], col[1], col[2], 0.20)), rounding=3.0)
            dl.add_rect(imgui_pt(x - hw, y - hh), imgui_pt(x + hw, y + hh),
                        col=_col(col), rounding=3.0, thickness=2.5)
            label = f"{r.get('name', '')}"
            if r.get("dps"):
                label += f" {r['dps']}"
            # 标签位置原样（x-hw, y-hh-15）；避让开关默认关，不改坐标
            lx, ly = _avoid_spot(x - hw, y - hh - 15.0, win_w, win_h, occupied)
            _text_outline(dl, lx, ly, label, INK)
        else:
            dl.add_circle(imgui_pt(x, y), 8.0, _col((col[0], col[1], col[2], 0.80)), 0, 1.8)
            dl.add_text(imgui_pt(x + 10.0, y - 6.0),
                        _col((col[0], col[1], col[2], 0.90)), str(i + 1))'''
    new_sel = '''        if sel:
            hw = 1.6 * tile_x * sx
            hh = 1.1 * tile_y * sy
            # 选中：柔和填充 + 外发光 + 四角括号（比实线方框更精致）
            _glow(dl, x, y, max(hw, hh) * 0.9, col, rings=3, base_alpha=0.16)
            dl.add_rect_filled(imgui_pt(x - hw, y - hh), imgui_pt(x + hw, y + hh),
                               col=_col((col[0], col[1], col[2], 0.22)), rounding=6.0)
            _brackets(dl, x - hw, y - hh, x + hw, y + hh, col, size=9.0, thickness=2.6)
            label = f"{r.get('name', '')}"
            if r.get("dps"):
                label += f" {r['dps']}"
            # 标签位置原样（x-hw, y-hh-15）；避让开关默认关，不改坐标
            lx, ly = _avoid_spot(x - hw, y - hh - 15.0, win_w, win_h, occupied)
            _chip(dl, lx, ly, label, INK, bg=_rgba(col, 0.22))
        else:
            _glow(dl, x, y, 6.5, col, rings=2, base_alpha=0.16)
            dl.add_circle_filled(imgui_pt(x, y), 2.5, _col(_rgba(col, 0.9)), 20)
            dl.add_circle(imgui_pt(x, y), 8.0, _col(_rgba(col, 0.8)), 28, 1.8)
            _text_outline(dl, x + 10.0, y - 6.0, str(i + 1), _rgba(col, 0.95))'''
    if old_sel in t:
        t = t.replace(old_sel, new_sel, 1)
    else:
        print("important anchor miss")
    open(p, "w", encoding="utf-8", newline=chr(10)).write(t)
    print("draw.py patched, bytes", len(t.encode()))
