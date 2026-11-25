# -*- coding: utf-8 -*-
"""玻璃拟态实时层与策略小窗（PIL 渲染 + Tk 承载）。

设计取舍：
- 用 PIL 画整帧再塞进 Tk（PhotoImage），比 Tk Canvas 抗锯齿好，也方便做渐变/圆角卡片；
- HUD 层必须点击穿透 + 不抢焦点（Win32 扩展风格），小窗层必须可交互，两层分开；
- 刷新按 1~2 fps 设计（ADB 抓帧 600~800ms），用 after(120) 的节拍做脉冲动画即可。
"""
import ctypes
import math
import os
import tkinter as tk

from PIL import Image, ImageDraw, ImageFont, ImageTk

TRANSPARENT_KEY = "#010203"
KEY_RGB = (1, 2, 3)

# 调色板：深底 + 青/琥珀双强调（避免大面积紫）
BG = (11, 15, 18)
CARD = (18, 24, 29)
CARD_HI = (24, 33, 40)
LINE = (38, 48, 56)
INK = (238, 241, 244)
GREY = (148, 159, 168)
DIM = (96, 107, 116)
CYAN = (94, 214, 214)
AMBER = (240, 196, 82)
CORAL = (232, 116, 96)
GREEN = (96, 200, 130)
BLUE = (120, 190, 230)

FONT_DIR = r"C:\Windows\Fonts"
_FONT_CACHE = {}


def font(size, bold=False):
    key = (size, bold)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    name = "msyhbd.ttc" if bold else "msyh.ttc"
    path = os.path.join(FONT_DIR, name)
    f = None
    try:
        f = ImageFont.truetype(path, size, index=0)
    except Exception:
        try:
            f = ImageFont.truetype("arialbd.ttf" if bold else "arial.ttf", size)
        except Exception:
            f = ImageFont.load_default()
    _FONT_CACHE[key] = f
    return f


def text(d, xy, s, size=11, fill=INK, bold=False, anchor="la"):
    d.text(xy, s, font=font(size, bold), fill=fill, anchor=anchor)


def rrect(d, box, r, fill=None, outline=None, width=1):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def chip(d, xy, s, fg, bg, size=9, padx=8, h=18):
    w = d.textlength(s, font=font(size)) + padx * 2
    x, y = xy
    rrect(d, [x, y, x + w, y + h], h / 2, fill=bg, outline=None)
    text(d, (x + padx, y + h / 2 - 1), s, size, fg, False, "lm")
    return w


# ---------------- 战术标注（draw_calls 契约，与算法侧 plan_marks 对齐） ----------------
# 颜色语义：target=琥珀实线框 / snipe=青色虚线框 / avoid=珊瑚斜纹框；
# 投放点 role：queen 青、king 橙、warden 紫灰、rc 珊瑚、troop 绿。
MARK_ROLE_COLORS = {
    "queen": CYAN,
    "king": (232, 152, 84),
    "warden": (158, 150, 190),
    "rc": CORAL,
    "troop": GREEN,
}

SPELL_COLORS = {"freeze": (140, 210, 240), "rage": (230, 110, 200), "invis": INK}


def _cell_px(calib):
    """用 (0,0)->(1,0) 的像素差估算单格边长。"""
    p0 = calib.tile_to_px(0, 0)
    p1 = calib.tile_to_px(1, 0)
    return max(2.0, ((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2) ** 0.5)


def _dashed_line(draw, p0, p1, color, dash=6, gap=5, width=1):
    x0, y0 = p0
    x1, y1 = p1
    dx, dy = x1 - x0, y1 - y0
    dist = (dx * dx + dy * dy) ** 0.5
    if dist < 1:
        return
    ux, uy = dx / dist, dy / dist
    s = 0.0
    while s < dist:
        e = min(s + dash, dist)
        draw.line([x0 + ux * s, y0 + uy * s, x0 + ux * e, y0 + uy * e],
                  fill=color, width=width)
        s = e + gap


def _dashed_rect(draw, box, color, dash=6, gap=5, width=2):
    x0, y0, x1, y1 = box
    _dashed_line(draw, (x0, y0), (x1, y0), color, dash, gap, width)
    _dashed_line(draw, (x1, y0), (x1, y1), color, dash, gap, width)
    _dashed_line(draw, (x1, y1), (x0, y1), color, dash, gap, width)
    _dashed_line(draw, (x0, y1), (x0, y0), color, dash, gap, width)


def _diagonal_hatch(draw, box, color, step=12, width=1):
    x0, y0, x1, y1 = box
    draw.rectangle(box, outline=color, width=2)
    for k in range(-int(y1 - y0), int(x1 - x0), step):
        _dashed_line(draw, (x0 + k, y0), (x1 + k, y1), color, step // 2, step // 2, width)


def _dashed_circle(draw, cx, cy, r, color, dash=6, gap=5, width=2):
    steps = 72
    pts = []
    for i in range(steps + 1):
        a = 2 * math.pi * i / steps
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    for i in range(steps):
        if i % 2 == 0:
            draw.line([pts[i], pts[i + 1]], fill=color, width=width)


def _arrow_head(draw, x0, y0, x1, y1, color, size=14):
    ang = math.atan2(y1 - y0, x1 - x0)
    for da in (-2.4, 2.4):
        a = ang + da
        draw.line([x1, y1, x1 - size * math.cos(a), y1 - size * math.sin(a)],
                  fill=color, width=3)


def render_marks(draw, calib, calls, t=0.0, show=("all",)):
    """把 draw_calls 契约画到 HUD 图层上。

    calls: {"marks":[...], "lines":[...], "pins":[...], "circles":[...], "steps":[...]}
    坐标 tile->px 一律走 calib.tile_to_px，不在此推公式。
    """
    calls = calls or {}
    # 1) 建筑标记：目标=琥珀实线 / 狙杀=青虚线 / 规避=珊瑚斜纹
    for m in calls.get("marks") or []:
        gx, gy = m.get("tile", [0, 0])
        px, py = calib.tile_to_px(gx, gy)
        role = m.get("role", "target")
        color = {"target": AMBER, "snipe": CYAN, "avoid": CORAL}.get(role, AMBER)
        half = _cell_px(calib) * max(1.5, int(m.get("size", 2))) / 2
        box = [px - half, py - half, px + half, py + half]
        if role == "snipe":
            _dashed_rect(draw, box, CYAN)
        elif role == "avoid":
            _diagonal_hatch(draw, box, CORAL)
        else:
            draw.rectangle(box, outline=AMBER, width=2)
        if m.get("label"):
            draw.text((px, py - half - 12), m["label"], font=font(9, True),
                      fill=color, anchor="ms")

    # 2) 穿云箭：青主线 + 末端大箭头，命中点小十字并标序号，中部标说明
    for ln in calls.get("lines") or []:
        fx, fy = ln.get("from", [0, 0])
        tx, ty = ln.get("to", [0, 0])
        x1, y1 = calib.tile_to_px(fx, fy)
        x2, y2 = calib.tile_to_px(tx, ty)
        draw.line([x1, y1, x2, y2], fill=CYAN, width=2)
        _arrow_head(draw, x1, y1, x2, y2, CYAN)
        for i, h in enumerate(ln.get("hits") or [], 1):
            hx, hy = calib.tile_to_px(h[0], h[1])
            draw.line([hx - 6, hy, hx + 6, hy], fill=AMBER, width=2)
            draw.line([hx, hy - 6, hx, hy + 6], fill=AMBER, width=2)
            draw.text((hx + 9, hy - 9), str(i), font=font(9, True), fill=AMBER)
        if ln.get("label"):
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            draw.text((mx, my - 14), ln["label"], font=font(9, True),
                      fill=CYAN, anchor="ms")

    # 3) 投放点：圆 + 左上序号徽章，hero 12px / troop 9px，troop 带 ×N，1.2s 呼吸脉冲
    for pin in calls.get("pins") or []:
        gx, gy = pin.get("tile", [0, 0])
        px, py = calib.tile_to_px(gx, gy)
        role = pin.get("role", "troop")
        col = MARK_ROLE_COLORS.get(role, GREEN)
        hero = role in ("queen", "king", "warden", "rc")
        r = 12 if hero else 9
        pulse = 0.85 + 0.15 * math.sin(t * 2 * math.pi / 1.2)
        rr = r * pulse
        draw.ellipse([px - rr, py - rr, px + rr, py + rr], outline=col, width=2)
        order = pin.get("order")
        if order:
            bx, by = px - r - 9, py - r - 9
            draw.ellipse([bx - 9, by - 9, bx + 9, by + 9], fill=col)
            draw.text((bx, by), str(order), font=font(9, True),
                      fill=(10, 20, 16), anchor="mm")
        if pin.get("count"):
            draw.text((px, py + r + 10), f"×{pin['count']}", font=font(9, True),
                      fill=col, anchor="mt")
        if pin.get("label"):
            draw.text((px, py - r - 16), pin["label"], font=font(9),
                      fill=INK, anchor="ms")

    # 4) 法术圈：虚线圆，freeze 冰蓝 / rage 品红 / invis 白
    for c in calls.get("circles") or []:
        gx, gy = c.get("tile", [0, 0])
        px, py = calib.tile_to_px(gx, gy)
        rp = _cell_px(calib) * float(c.get("radius", 4))
        _dashed_circle(draw, px, py, rp, SPELL_COLORS.get(c.get("kind"), INK))


# ---------------- 覆盖层 ----------------

def render_overlay(size, info, plans=None, heat=None, layout=None, t=0.0,
                   marks=None, legend=True):
    """把整块 HUD 画成一张 RGBA 图；背景保持 key 色以便透明。"""
    w, h = size
    img = Image.new("RGBA", (w, h), KEY_RGB + (255,))
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    quad = (info.get("boundary") or {}).get("quad")
    if quad:
        quad = [tuple(p) for p in quad]
        d.line(quad + [quad[0]], fill=(255, 255, 255, 46), width=1)

        n = 44
        cx = sum(p[0] for p in quad) / 4
        cy = sum(p[1] for p in quad) / 4
        kx = (quad[1][0] - quad[3][0]) / (2 * n)
        ky = (quad[2][1] - quad[0][1]) / (2 * n)

        # 热区（如果有）
        if heat is not None:
            try:
                hx, hy = heat.shape
                for gx in range(0, hx, 2):
                    for gy in range(0, hy, 2):
                        v = float(heat[gx, gy])
                        if not (0 < v < 10):
                            continue
                        a = int(min(120, 18 + v * 160))
                        px = cx + (gx - gy) * kx
                        py = cy + (gx + gy - n) * ky
                        d.polygon([(px, py - ky), (px + kx, py), (px, py + ky), (px - kx, py)],
                                  fill=(232, 110, 96, a) if v > 0.2 else (96, 170, 232, a))
            except Exception:
                pass

        for g in range(0, n + 1, 4):
            p1 = (quad[0][0] + (quad[1][0] - quad[0][0]) * g / n,
                  quad[0][1] + (quad[1][1] - quad[0][1]) * g / n)
            p2 = (quad[3][0] + (quad[2][0] - quad[3][0]) * g / n,
                  quad[3][1] + (quad[2][1] - quad[3][1]) * g / n)
            d.line([p1, p2], fill=(255, 255, 255, 30), width=1)

        # 防御射程环
        if layout:
            for b in layout.get("buildings", []):
                rng = (b.get("range") or 0)
                if not rng:
                    continue
                gx, gy = b["tile"]
                px = cx + (gx - gy) * kx
                py = cy + (gx + gy - n) * ky
                rr = rng * abs(kx) * 1.6
                if rr > 4:
                    d.ellipse([px - rr, py - rr, px + rr, py + rr], outline=(120, 190, 230, 40), width=1)

        # 入点 + 路径 + 脉冲
        if plans:
            for pl in plans:
                col = {"A": GREEN, "B": AMBER, "C": BLUE}.get(pl.get("id"), GREEN)
                path = (pl.get("path") or {}).get("path") or []
                if len(path) > 1:
                    pts = []
                    for p in path[::2]:
                        px = cx + (p[0] - p[1]) * kx
                        py = cy + (p[0] + p[1] - n) * ky
                        pts.append((px, py))
                    d.line(pts, fill=col + (150,), width=2)
                    if len(pts) > 2:
                        d.line(pts[-3:], fill=col + (230,), width=3)
                for e in pl.get("entries", []):
                    gx, gy = e["tile"]
                    px = cx + (gx - gy) * kx
                    py = cy + (gx + gy - n) * ky
                    pulse = 0.55 + 0.45 * abs(math.sin(t * 0.9))
                    r0 = 9 + 8 * pulse
                    d.ellipse([px - r0, py - r0, px + r0, py + r0], outline=col + (int(90 * pulse),), width=2)
                    d.ellipse([px - 7, py - 7, px + 7, py + 7], fill=col + (235,))
                    text(d, (px, py - 0.5), f"{pl['id']}{e.get('troops', '')}", 9, (10, 20, 16), True, "mm")

    # 战术标注：建筑框 / 穿云箭 / 投放点 / 法术圈
    if marks:
        try:
            from .geo import Calib
            quad = (info.get("boundary") or {}).get("quad")
            if quad:
                render_marks(d, Calib.from_quad(quad), marks, t)
        except Exception:
            pass

    # 左下角图例
    if legend:
        lx, ly = 18, h - 178
        rrect(d, [lx - 8, ly - 8, lx + 318, ly + 118], 8,
              fill=(12, 18, 22, 205), outline=(46, 56, 64, 180))
        text(d, (lx, ly), "图例", 10, INK, True)
        rows = [
            (AMBER, "琥珀实线=目标建筑  青虚线=狙杀  珊瑚斜纹=规避"),
            (CYAN, "投放点：女王青 国王橙 守护者紫灰 战宠珊瑚 部队绿"),
            (SPELL_COLORS["freeze"], "虚线圆=法术圈(freeze冰蓝/rage品红/invis白)"),
            (CYAN, "青箭头=穿云箭轨迹 · 十字=命中点"),
        ]
        yy = ly + 18
        for col, label in rows:
            d.ellipse([lx, yy + 3, lx + 8, yy + 11], fill=col)
            text(d, (lx + 14, yy), label, 9, GREY, False, "lm")
            yy += 24

    return Image.alpha_composite(img, layer).convert("RGB")
    dash = info.get("dash") or {}
    bar = [16, 14, 470, 66]
    rrect(d, bar, 10, fill=(16, 22, 26, 210), outline=(52, 64, 72, 200))
    dot = GREEN if dash.get("ok") else CORAL
    d.ellipse([28, 27, 38, 37], fill=dot + (255,))
    text(d, (46, 22), f"CLASH LAB · {dash.get('state', '待机')}", 12, INK, True)
    text(d, (46, 40), f"{dash.get('detail', '')}", 9, DIM)
    if dash.get("marks"):
        text(d, (46, 56), f"标注 {dash['marks']}", 9, CYAN)
    if dash.get("fps"):
        chip(d, (bar[2] - 118, 20), f"{dash['fps']:.1f} fps", CYAN, (22, 40, 42, 230))
    if dash.get("conf") is not None:
        chip(d, (bar[2] - 118, 38), f"标定 {dash['conf']:.2f}", AMBER, (42, 36, 20, 230))

    if plans:
        y = h - 58
        rrect(d, [16, y, 400, y + 34], 8, fill=(16, 22, 26, 190), outline=(46, 56, 64, 170))
        text(d, (28, y + 17), "A 强攻", 9, GREEN, False, "lm")
        text(d, (88, y + 17), "B 双线", 9, AMBER, False, "lm")
        text(d, (150, y + 17), "C 盲区", 9, BLUE, False, "lm")
        text(d, (212, y + 17), "冷区=C 入口 · 亮红=高 dps", 9, DIM, False, "lm")

    return Image.alpha_composite(img, layer).convert("RGB")


# ---------------- 策略小窗 ----------------

PANEL_W, PANEL_H = 432, 604


def render_panel(size, state, report=None, plans=None, llm_view=None, selected="A",
                 steps=None, footer=None):
    w, h = size
    img = Image.new("RGBA", (w, h), BG + (255,))
    d = ImageDraw.Draw(img)

    # 顶部品牌条
    rrect(d, [0, 0, w, 66], 0, fill=(14, 19, 23, 255))
    text(d, (20, 16), "战术中枢", 15, INK, True)
    text(d, (20, 42), "TACTIC CONSOLE · TH13", 9, DIM)
    ok = bool(state.get("connected"))
    chip(d, (w - 108, 22), "在线" if ok else "离线", GREEN if ok else CORAL,
         (22, 44, 32, 255) if ok else (46, 24, 24, 255), size=9, padx=10, h=20)

    # 方案卡
    plan_list = plans or []
    y = 74
    for pl in plan_list[:3]:
        col = {"A": GREEN, "B": AMBER, "C": BLUE}.get(pl.get("id"), GREEN)
        hi = pl.get("id") == selected
        box = [14, y, w - 14, y + 100]
        rrect(d, box, 12, fill=CARD_HI if hi else CARD, outline=col + (200,) if hi else LINE, width=1)
        rrect(d, [box[0] + 1, y + 1, box[0] + 4, box[3] - 1], 2, fill=col + (255,) if hi else col + (110,))
        text(d, (box[0] + 14, y + 9), f"{pl.get('id')}  {pl.get('name')}", 12, INK, True)
        pred = pl.get("predicted", 0.0)
        risk = pl.get("risk", "-")
        rcol = {"低": GREEN, "中": AMBER, "高": CORAL}.get(risk, GREY)
        chip(d, (box[2] - 84, y + 7), f"风险 {risk}", rcol, (26, 32, 36, 255), size=8, padx=7, h=16)
        chip(d, (box[2] - 84, y + 26), f"预测 {pred:.2f}", CYAN, (18, 36, 38, 255), size=8, padx=7, h=16)
        pb = [box[0] + 14, y + 47, box[2] - 14, y + 51]
        rrect(d, pb, 2, fill=(30, 38, 44, 255))
        rrect(d, [pb[0], pb[1], pb[0] + (pb[2] - pb[0]) * min(pred * 3.2, 1.0), pb[3]], 2, fill=col + (220,))
        ents = "  /  ".join(f"({e['tile'][0]},{e['tile'][1]})×{e.get('troops', '?')}" for e in pl.get("entries", []))
        text(d, (box[0] + 14, y + 57), ents, 9, (198, 208, 216))
        pth = pl.get("path") or {}
        text(d, (box[0] + 14, y + 76), f"路径 {pth.get('steps', '-')} 格 · {pth.get('time_s', '-')}s · "
                                       f"承伤 {pl.get('exposure', pth.get('exposure', '-'))}", 9, DIM)
        y += 106

    # 首打顺序 + 研究结论
    if report:
        pri = report.get("priority") or []
        if pri:
            text(d, (20, y + 2), "首打顺序", 10, GREY, True)
            x = 20
            for i, p in enumerate(pri[:3]):
                label = f"{i+1}. {p['type']}({p['tile'][0]},{p['tile'][1]})"
                cw = chip(d, (x, y + 18), label, INK, (26, 34, 40, 255), size=8, padx=7, h=17)
                x += cw + 6
                if x > w - 110:
                    break
            y += 40
        notes = report.get("notes") or []
        if notes:
            text(d, (20, y), "研究结论", 10, GREY, True)
            yy = y + 16
            line = notes[0]
            for wl in [line[i:i + 42] for i in range(0, min(len(line), 84), 42)]:
                text(d, (20, yy), wl, 9, (200, 209, 216))
                yy += 13
            y = yy + 2

    # 执行顺序（来自 draw_calls.steps，最多 6 条，点前 24px 热区回调 step:N）
    hit_steps = {}
    if steps:
        # 兼容：规则侧 steps 为字符串列表，统一归一为 {order,text,role}
        steps = [s if isinstance(s, dict) else {"order": i + 1, "text": str(s), "role": ""}
                 for i, s in enumerate(steps[:6])]
        text(d, (20, y + 2), "执行顺序", 10, GREY, True)
        y += 18
        for i, st in enumerate(steps[:6]):
            col = MARK_ROLE_COLORS.get(st.get("role"), GREEN)
            badge = st.get("order", i + 1)
            rrect(d, [20, y, w - 20, y + 24], 6, fill=(24, 32, 38, 255), outline=LINE)
            d.ellipse([30, y + 6, 42, y + 18], fill=col)
            text(d, (36, y + 12), str(badge), 9, (10, 20, 16), True, "mm")
            # 条目带 card:"k012" 时尾部画青色小 chip；纯文本步骤不画，不报错
            card = st.get("card")
            tail_x = w - 34
            if card:
                chip(d, (tail_x - 58, y + 4), f"[{card}]", CYAN, (18, 36, 38, 255),
                     size=8, padx=6, h=16)
                tail_x -= 66
            # 文本按剩余宽度截断，避免压到 chip
            body = st.get("text", "")
            max_w = tail_x - 56
            while body and d.textlength(body, font=font(9)) > max_w:
                body = body[:-1]
            text(d, (50, y + 12), body, 9, INK, False, "lm")
            hit_steps[f"step:{i + 1}"] = (20, y, w - 20, y + 24)
            y += 28

    # 画像/参考小字 footer（UI 层自组装，无内容不画；贴近复核盒则跳过防挤）
    if footer and y < h - 140:
        text(d, (20, y + 4), footer, 8, (120, 138, 148), False)

    # 模型复核
    box = [14, h - 124, w - 14, h - 46]
    rrect(d, box, 12, fill=(16, 22, 27, 255), outline=LINE)
    text(d, (box[0] + 12, box[1] + 7), "大模型复核", 10, GREY, True)
    if llm_view:
        st = llm_view.get("status", "")
        col = {"ok": GREEN, "rejected": CORAL, "error": CORAL}.get(st, AMBER)
        label = {"ok": "已通过校验", "rejected": "被校验拒绝", "error": "调用失败",
                 "pending": "调用中"}.get(st, st)
        chip(d, (box[2] - 90, box[1] + 5), label, col, (26, 32, 36, 255), size=8, padx=7, h=16)
        body = llm_view.get("text") or "—"
        for i, line in enumerate([body[j:j + 46] for j in range(0, min(len(body), 92), 46)]):
            text(d, (box[0] + 12, box[1] + 24 + i * 13), line, 9, (198, 208, 215))
    else:
        text(d, (box[0] + 12, box[1] + 26), "未调用：点底部按钮让 ds / glm 复核当前方案", 9, DIM)

    # 底部按钮
    by = h - 40
    btns = [("研究图", 14, 148), ("重跑研究", 166, 124), ("复制计划", 294, 124)]
    for label, bx, bw in btns:
        rrect(d, [bx, by, bx + bw, by + 30], 9, fill=(24, 32, 38, 255), outline=(52, 62, 70, 255))
        text(d, (bx + bw / 2, by + 15), label, 10, INK, False, "mm")

    return img.convert("RGB"), {"buttons": {label: (bx, by, bx + bw, by + 30) for label, bx, bw in btns},
                                "cards": {pl.get("id"): (14, 74 + i * 106, w - 14, 74 + i * 106 + 100)
                                          for i, pl in enumerate(plan_list[:3])},
                                "steps": hit_steps}


def _top_hwnd(win):
    hwnd = win.winfo_id()
    parent = ctypes.windll.user32.GetParent(hwnd)
    return parent or hwnd


def make_click_through(win):
    GWL_EXSTYLE = -20
    WS_EX_LAYERED = 0x00080000
    WS_EX_TRANSPARENT = 0x00000020
    WS_EX_NOACTIVATE = 0x08000000
    WS_EX_TOOLWINDOW = 0x00000080
    hwnd = _top_hwnd(win)
    ex = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    ctypes.windll.user32.SetWindowLongW(
        hwnd, GWL_EXSTYLE, ex | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW)
    return hwnd


def make_draggable(win, handle):
    def start(e):
        win._dx, win._dy = e.x_root - win.winfo_x(), e.y_root - win.winfo_y()

    def move(e):
        win.geometry(f"+{e.x_root - win._dx}+{e.y_root - win._dy}")

    handle.bind("<Button-1>", start)
    handle.bind("<B1-Motion>", move)


class TacticConsole:
    """覆盖层 + 策略小窗的宿主，外部只需 update(info, report, plans, llm_view)。"""

    def __init__(self, width=1280, height=720, overlay=True, panel=True, on_action=None):
        self.width, self.height = width, height
        self.on_action = on_action
        self.overlay_enabled, self.panel_enabled = overlay, panel
        self.t = 0.0
        self.master = None
        self.ov = self.ov_lbl = None
        self.pn = self.pn_lbl = None
        self.info, self.report, self.plans, self.llm_view = {}, None, None, None
        self.marks = None
        self.footer = None
        self._photos = []
        self.hit = {}

    def attach(self, master):
        """挂到主窗口主线程：面板/覆盖层都建在主 Tk 下，渲染由主线程 after 循环驱动。

        Windows 下第二 Tk 线程会触发 Tcl apartment 冲突，因此不再自建 Tk/mainloop。
        """
        self.master = master
        if self.overlay_enabled:
            self.ov = tk.Toplevel(master)
            self.ov.overrideredirect(True)
            self.ov.geometry(f"{self.width}x{self.height}+0+0")
            self.ov.configure(bg=TRANSPARENT_KEY)
            try:
                self.ov.attributes("-transparentcolor", TRANSPARENT_KEY)
            except Exception:
                pass
            self.ov.attributes("-topmost", True)
            self.ov_lbl = tk.Label(self.ov, bg=TRANSPARENT_KEY)
            self.ov_lbl.pack()
            make_click_through(self.ov)
        else:
            self.ov = None

        if self.panel_enabled:
            pw, ph = PANEL_W, PANEL_H
            self.pn = tk.Toplevel(master)
            self.pn.overrideredirect(True)
            self.pn.geometry(f"{pw}x{ph}+{max(20, self.width - pw - 28)}+64")
            self.pn.configure(bg="#0b0f12")
            self.pn.attributes("-topmost", True)
            self.pn_lbl = tk.Label(self.pn, bg="#0b0f12", bd=0)
            self.pn_lbl.pack()
            self.pn_lbl.bind("<Button-1>", self._on_click)
            make_draggable(self.pn, self.pn_lbl)
        else:
            self.pn = None

        self.master.after(0, self._render)
        self.master.after(120, self._tick)

    # ---------- 事件 ----------
    def _on_click(self, e):
        for key, box in (self.hit.get("steps") or {}).items():
            if box[0] <= e.x <= box[2] and box[1] <= e.y <= box[3]:
                if self.on_action:
                    self.on_action(key)
                return
        for label, box in (self.hit.get("buttons") or {}).items():
            if box[0] <= e.x <= box[2] and box[1] <= e.y <= box[3]:
                if self.on_action:
                    self.on_action(label.lower())
                return
        for pid, box in (self.hit.get("cards") or {}).items():
            if box[0] <= e.x <= box[2] and box[1] <= e.y <= box[3]:
                if self.on_action:
                    self.on_action("card:" + str(pid))
                return

    # ---------- 刷新 ----------
    def update_state(self, info=None, report=None, plans=None, llm_view=None, marks=None,
                     footer=None):
        if info is not None:
            self.info = info
        if report is not None:
            self.report = report
        if plans is not None:
            self.plans = plans
        if llm_view is not None:
            self.llm_view = llm_view
        if marks is not None:
            self.marks = marks
        if footer is not None:
            self.footer = footer
        # 渲染由主线程 _tick 驱动，update_state 只存数据。

    def _render(self):
        if self.ov is not None:
            img = render_overlay((self.width, self.height), self.info, self.plans,
                                 heat=self.info.get("heat"), layout=self.info.get("layout"),
                                 t=self.t, marks=self.marks)
            photo = ImageTk.PhotoImage(img)
            self.ov_lbl.configure(image=photo)
            self._photos = [photo]
        if self.pn is not None:
            steps = (self.marks or {}).get("steps")
            img, hit = render_panel((PANEL_W, PANEL_H), self.info, self.report, self.plans,
                                    self.llm_view, self.info.get("selected", "A"),
                                    steps=steps, footer=self.footer)
            self.hit = hit
            photo = ImageTk.PhotoImage(img)
            self.pn_lbl.configure(image=photo)
            self._photos.append(photo)

    def _tick(self):
        self.t += 0.12
        self._render()
        if self.master is not None:
            self.master.after(120, self._tick)


if __name__ == "__main__":
    demo_plans = [
        {"id": "A", "name": "单点强攻", "predicted": 0.19, "risk": "低", "exposure": 15895,
         "entries": [{"tile": [8, 16], "troops": 7}], "path": {"steps": 15, "time_s": 10.0}},
        {"id": "B", "name": "双线分离", "predicted": 0.19, "risk": "低", "exposure": 15895,
         "entries": [{"tile": [8, 16], "troops": 4}, {"tile": [36, 28], "troops": 3}],
         "path": {"steps": 15, "time_s": 10.0}},
        {"id": "C", "name": "弱侧渗透", "predicted": 0.17, "risk": "中", "exposure": 18400,
         "entries": [{"tile": [1, 22], "troops": 7}], "path": {"steps": 22, "time_s": 14.7}},
    ]
    demo_report = {"priority": [{"type": "scattershot", "tile": [32, 32]},
                                {"type": "eagle-artillery", "tile": [30, 14]}],
                   "notes": ["最优切入在 203° 扇区（格 8,16），模拟得分 0.19，该点覆盖 dps 566。"]}
    app = TacticConsole()
    app.update_state(info={"connected": True, "dash": {"ok": True, "state": "研究", "fps": 1.2,
                                                       "conf": 0.83, "detail": "sample layout"},
                            "boundary": {"quad": [[697, 107], [944, 351], [672, 585], [347, 327]]}},
                     report=demo_report, plans=demo_plans,
                     llm_view={"status": "ok", "text": "203° 单点强攻可行，建议先拆 (32,32) 散射炮。"})
    app.run()
