# -*- coding: utf-8 -*-
"""把分析结果画回画面：实时绘制层 + 小窗策略面板的合成预览。"""
import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np

FONT_REG = r"C:\Windows\Fonts\msyh.ttc"
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"

YELLOW = (240, 196, 82)
ORANGE = (226, 122, 56)
GREEN = (96, 200, 130)
BLUE = (120, 190, 235)
WHITE = (238, 240, 242)
GREY = (150, 156, 160)
DARK = (18, 22, 26)
PANEL_BG = (16, 20, 24)

BUILD_CN = {
    "town-hall": "大本营", "eagle-artillery": "鹰火炮", "scattershot": "散射炮",
    "inferno-tower": "地狱塔", "x-bow": "连弩", "cannon": "加农炮",
    "archer-tower": "箭塔", "wizard-tower": "法师塔", "air-defense": "防空",
    "mortar": "迫击炮", "air-sweeper": "吹风机", "hidden-tesla": "特斯拉",
    "bomb-tower": "炸弹塔", "spell-tower": "法术塔", "defense": "防御",
}

_font_cache = {}


def font(size, bold=False):
    key = (size, bold)
    if key in _font_cache:
        return _font_cache[key]
    path = FONT_BOLD if bold else FONT_REG
    try:
        f = ImageFont.truetype(path, size)
    except Exception:
        f = ImageFont.load_default()
    _font_cache[key] = f
    return f


def _bgr_to_rgb(frame):
    return Image.fromarray(frame[:, :, ::-1]).convert("RGB")


def _dashed_line(draw, p1, p2, color, width=1, dash=8, gap=5):
    x1, y1 = p1
    x2, y2 = p2
    length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    if length < 1:
        return
    n = int(length // (dash + gap))
    for i in range(n + 1):
        s = i * (dash + gap) / length
        e = min((i * (dash + gap) + dash) / length, 1.0)
        draw.line([(x1 + (x2 - x1) * s, y1 + (y2 - y1) * s),
                   (x1 + (x2 - x1) * e, y1 + (y2 - y1) * e)], fill=color, width=width)


def draw_overlay(base_img, info, calib=None, plan=None):
    """在帧上绘制事实层、风险层、建议层。返回 PIL.Image。"""
    if isinstance(base_img, np.ndarray):
        img = _bgr_to_rgb(base_img).convert("RGBA")
    else:
        img = base_img.convert("RGBA")
    W, H = img.size
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    # 事实层：地图菱形 + 网格点
    if calib is not None:
        quad = [tuple(map(float, p)) for p in calib.quad]
        d.line(quad + [quad[0]], fill=(255, 255, 255, 150), width=1)
        for gx, gy, (px, py) in calib.grid_points(step=4):
            d.ellipse([px - 1.6, py - 1.6, px + 1.6, py + 1.6], fill=(255, 255, 255, 55))

    # 风险层：核心区
    if calib is not None:
        n = calib.n
        core = [(12, 12), (n - 12, 12), (n - 12, n - 12), (12, n - 12)]
        pts = [calib.tile_to_px(gx, gy) for gx, gy in core]
        _dashed_line(d, pts[0], pts[1], ORANGE + (190,))
        _dashed_line(d, pts[1], pts[2], ORANGE + (190,))
        _dashed_line(d, pts[2], pts[3], ORANGE + (190,))
        _dashed_line(d, pts[3], pts[0], ORANGE + (190,))

    # 识别层：建筑外框与类型
    for b in (info.get("buildings") or []):
        x, y, w, h = b["box"]
        typed = bool(b.get("type"))
        col = (255, 176, 64, 225) if typed else (150, 160, 170, 170)
        d.rectangle([x, y, x + w, y + h], outline=col, width=2)
        label = BUILD_CN.get(b["type"], "建筑") if typed else "未知"
        tw = d.textlength(label, font=font(12))
        d.rectangle([x, y - 16, x + tw + 8, y - 1], fill=(12, 16, 20, 220))
        d.text((x + 4, y - 15), label, font=font(12), fill=col)

    # 建议层：撒兵点、编号、箭头、法术
    if plan and calib is not None:
        core_px = calib.tile_to_px(calib.n / 2, calib.n / 2)
        for e in plan["entry"]:
            px, py = calib.tile_to_px(*e["tile"])
            r = 15
            d.ellipse([px - r, py - r, px + r, py + r], fill=GREEN + (235,), outline=(20, 40, 26, 255))
            tw = d.textlength(str(e["step"]), font=font(16, True))
            d.text((px - tw / 2, py - 9), str(e["step"]), font=font(16, True), fill=(12, 26, 16))
            # 箭头指向核心
            dx, dy = core_px[0] - px, core_px[1] - py
            ln = max((dx * dx + dy * dy) ** 0.5, 1)
            ex, ey = px + dx / ln * 62, py + dy / ln * 62
            d.line([(px, py), (ex, ey)], fill=YELLOW + (235,), width=3)
            d.polygon([(ex, ey),
                       (ex - dx / ln * 12 - dy / ln * 6, ey - dy / ln * 12 + dx / ln * 6),
                       (ex - dx / ln * 12 + dy / ln * 6, ey - dy / ln * 12 - dx / ln * 6)],
                      fill=YELLOW + (235,))
            d.text((px + 20, py - 26), f"{e['score']:.2f}", font=font(12), fill=YELLOW + (230,))
        for s in plan.get("spells", []):
            px, py = calib.tile_to_px(*s["tile"])
            d.ellipse([px - 34, py - 34, px + 34, py + 34], outline=BLUE + (220,), width=2)
            d.text((px - 14, py - 8), "法术", font=font(13), fill=BLUE + (240,))

    img = Image.alpha_composite(img, layer)
    return img.convert("RGB")


def draw_hud(img, info, plan=None, panel_w=330, mini=False):
    """右侧小窗策略面板 + 顶部状态条，返回合成图。"""
    img = img.convert("RGB")
    W, H = img.size
    out = img.copy()
    d = ImageDraw.Draw(out)

    # 顶部状态条
    d.rectangle([0, 0, W, 34], fill=(10, 12, 14))
    state = info.get("state", "unknown")
    d.text((12, 8), f"状态 {state}", font=font(15, True), fill=WHITE)
    d.text((130, 9), f"标定 {info.get('boundary', {}).get('source') or '无'}  "
                     f"误差 {info.get('reproj') if info.get('reproj') is not None else '-'} px  "
                     f"红区 {info.get('red_ratio', 0):.2f}",
           font=font(13), fill=GREY)
    d.text((W - 150, 9), "F9 隐藏  F10 暂停", font=font(12), fill=(120, 126, 130))

    if mini:
        return out

    # 右侧面板
    x0 = W - panel_w - 14
    y0 = 48
    panel_h = min(H - 64, 470)
    d.rounded_rectangle([x0, y0, x0 + panel_w, y0 + panel_h], radius=10,
                        fill=PANEL_BG, outline=(70, 82, 90), width=1)

    d.text((x0 + 14, y0 + 12), "作战计划", font=font(16, True), fill=WHITE)
    steps = plan["entry"] if plan else []
    d.text((x0 + panel_w - 60, y0 + 14), f"{len(steps)} 步", font=font(13), fill=GREY)
    d.line([x0 + 14, y0 + 40, x0 + panel_w - 14, y0 + 40], fill=(48, 56, 62), width=1)

    y = y0 + 50
    for i, e in enumerate(steps):
        bg = (58, 72, 58) if i == 0 else (36, 42, 46)
        d.rectangle([x0 + 12, y, x0 + panel_w - 12, y + 34], fill=bg)
        d.text((x0 + 20, y + 8), f"{e['step']}  撒兵 @ 格 {e['tile'][0]},{e['tile'][1]}",
               font=font(13), fill=WHITE if i == 0 else (190, 196, 200))
        d.text((x0 + panel_w - 66, y + 9), f"{e['score']:.2f}", font=font(12), fill=YELLOW)
        y += 38
    if not steps:
        d.text((x0 + 16, y + 6), "未生成计划：缺少建筑清单", font=font(13), fill=GREY)
        y += 40

    # 置信度
    conf = plan.get("predicted", 0.0) if plan else 0.0
    d.text((x0 + 14, y + 6), f"预测得分 {conf:.2f}", font=font(13), fill=(160, 210, 175))
    d.rectangle([x0 + 14, y + 28, x0 + panel_w - 14, y + 40], fill=(38, 44, 48))
    d.rectangle([x0 + 14, y + 28, x0 + 14 + int((panel_w - 28) * min(conf, 1.0)), y + 40],
                fill=(96, 200, 130))
    y += 54

    # 解说
    d.text((x0 + 14, y + 4), "解说", font=font(12), fill=(130, 150, 160))
    note = info.get("note") or "外侧防御密度最高，建议正面突破后转点。"
    d.multiline_text((x0 + 14, y + 24), note, font=font(12), fill=(205, 212, 218), spacing=6)
    y += 24 + 18 * (note.count("\n") + 1) + 10

    # 接管按钮
    if y + 40 < y0 + panel_h:
        d.rounded_rectangle([x0 + 12, y, x0 + panel_w - 12, y + 36], radius=8,
                            fill=(88, 34, 34), outline=(160, 64, 64), width=1)
        label = "SPACE  接管"
        tw = d.textlength(label, font=font(13, True))
        d.text((x0 + panel_w / 2 - tw / 2, y + 9), label, font=font(13, True), fill=(238, 200, 200))

    return out


def save(img, path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    img.save(path)
    return path
