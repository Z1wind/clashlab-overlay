# -*- coding: utf-8 -*-
"""美化 topdown 渲染：深色底板 + 圆角建筑 + 阴影 + 图例/标题栏。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "topdown.py")
t = open(p, encoding="utf-8").read()

start = t.index("def render_topdown(layout, out_png, cell=24, grid=None):")
end = t.index("def export_2d_json(layout, out_json):")
new_fn = '''# ---------------------------------------------------------------- 美化绘制
def _rounded_rect(img, x0, y0, x1, y1, r, color, thickness=-1):
    """抗锯齿圆角矩形（矩形 + 四角圆补丁）。"""
    r = max(0, min(int(r), (x1 - x0) // 2, (y1 - y0) // 2))
    cv2.rectangle(img, (x0 + r, y0), (x1 - r, y1), color, thickness)
    cv2.rectangle(img, (x0, y0 + r), (x1, y1 - r), color, thickness)
    for cx, cy in ((x0 + r, y0 + r), (x1 - r, y0 + r), (x0 + r, y1 - r), (x1 - r, y1 - r)):
        cv2.circle(img, (cx, cy), r, color, thickness)


def _text_outline(img, text, org, scale, col, outline=(8, 10, 14), th=1):
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        cv2.putText(img, text, (org[0] + dx, org[1] + dy), cv2.FONT_HERSHEY_SIMPLEX,
                    scale, outline, th + 1, cv2.LINE_AA)
    cv2.putText(img, text, org, cv2.FONT_HERSHEY_SIMPLEX, scale, col, th, cv2.LINE_AA)


def _bg_gradient(h, w, top=(26, 20, 16), bottom=(38, 30, 24)):
    """竖向渐变（BGR）。"""
    ramp = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None, None]
    img = (np.array(top, np.float32)[None, None, :] * (1 - ramp)
           + np.array(bottom, np.float32)[None, None, :] * ramp)
    return np.repeat(img.astype(np.uint8), w, axis=1)


def render_topdown(layout, out_png, cell=24, grid=None):
    """layout dict -> 2D 俯视 PNG。返回 (w, h, n_buildings, n_walls)。"""
    if cv2 is None:
        raise RuntimeError("opencv required")
    g = int(grid or layout.get("grid", GRID))
    walls = layout.get("walls") or []
    buildings = layout.get("buildings") or []
    margin, hud_h = 26, 54
    w = h = g * cell + margin * 2
    img = _bg_gradient(h, w, top=(30, 22, 18), bottom=(46, 36, 28))
    # 外框 + 内底板
    _rounded_rect(img, 2, 2, w - 3, h - 3, 16, (58, 70, 86), 2)
    _rounded_rect(img, margin - 6, margin + hud_h - 6, w - margin + 6, h - margin + 6, 12, (22, 28, 36), -1)
    # 网格：细线 + 交点小点
    ox, oy = margin, margin + hud_h
    for i in range(g + 1):
        cv2.line(img, (ox, oy + i * cell), (ox + g * cell, oy + i * cell), (44, 54, 66), 1, cv2.LINE_AA)
        cv2.line(img, (ox + i * cell, oy), (ox + i * cell, oy + g * cell), (44, 54, 66), 1, cv2.LINE_AA)
    for i in range(0, g + 1, 4):
        for j in range(0, g + 1, 4):
            cv2.circle(img, (ox + i * cell, oy + j * cell), 1, (70, 84, 100), -1, cv2.LINE_AA)
    # 墙：深灰蓝小方块 + 顶部高光
    for x, y in walls:
        if 0 <= int(x) < g and 0 <= int(y) < g:
            px, py = ox + int(x) * cell, oy + int(y) * cell
            cv2.rectangle(img, (px + 1, py + 1), (px + cell - 2, py + cell - 2), (86, 98, 114), -1, cv2.LINE_AA)
            cv2.line(img, (px + 2, py + 2), (px + cell - 3, py + 2), (128, 142, 160), 1, cv2.LINE_AA)
    # 建筑：阴影 -> 圆角主体 -> 顶部高光 -> 深色描边 -> 标签
    for b in buildings:
        tp = str(b.get("type") or "")
        tx, ty = b.get("tile") or (0, 0)
        k = _size(tp)
        bx = ox + (int(tx) - (k - 1) // 2) * cell
        by = oy + (int(ty) - (k - 1) // 2) * cell
        bw = k * cell
        col = CATEGORY_COLOR[_category(tp)]
        _rounded_rect(img, bx + 3, by + 4, bx + bw - 1, by + bw, 5, (18, 22, 30), -1)  # 阴影
        _rounded_rect(img, bx + 2, by + 2, bx + bw - 3, by + bw - 3, 4, col, -1)
        light = tuple(min(255, c + 46) for c in col)
        cv2.line(img, (bx + 4, by + 4), (bx + bw - 6, by + 4), light, 2, cv2.LINE_AA)
        cv2.rectangle(img, (bx + 2, by + 2), (bx + bw - 3, by + bw - 3), (24, 28, 36), 1, cv2.LINE_AA)
        short = tp.replace("-", " ")[:7]
        _text_outline(img, short, (bx + 5, by + bw // 2 + 9), 0.30, (245, 248, 252))
    # 标题栏
    _rounded_rect(img, margin, 12, w - margin, 12 + hud_h - 16, 10, (16, 21, 28), -1)
    cv2.line(img, (margin + 10, 30), (margin + 26, 30), (61, 163, 232), 3, cv2.LINE_AA)
    _text_outline(img, "ClashLab  ·  2D top-down", (margin + 34, 36), 0.52, (243, 247, 251))
    _text_outline(img, "grid %d  buildings %d  walls %d" % (g, len(buildings), len(walls)),
                  (margin + 300, 36), 0.42, (170, 186, 204))
    # 图例
    lx, ly = margin + 10, h - margin - 2
    for label, ckey in (("大本营", "town-hall"), ("防御", "defense"), ("资源", "storage"),
                        ("兵营", "army"), ("其它", "other")):
        col = CATEGORY_COLOR[ckey]
        _rounded_rect(img, lx, ly - 12, lx + 14, ly + 2, 3, col, -1)
        _text_outline(img, label, (lx + 20, ly), 0.38, (210, 220, 232))
        lx += 78
    cv2.imencode(".png", img)[1].tofile(out_png)
    return img.shape[1], img.shape[0], len(buildings), len(walls)


'''
t = t[:start] + new_fn + t[end:]
open(p, "w", encoding="utf-8", newline=chr(10)).write(t)
print("topdown rewritten,", len(t.encode()), "B")
