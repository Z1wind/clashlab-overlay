# -*- coding: utf-8 -*-
"""schema v2 程序化路线图渲染器（纯离屏，禁启窗口/抓屏/联网）。

输入 plan.json 的 phases / threats / win_condition（schema v2，见 tactics.py
_validate_plan_v2）+ 底图 + quad，输出叠加路线图 PNG：
  - route  -> 虚线箭头 + 阶段序号圆标（阶段配色循环）
  - targets -> 瞄准圈 + ≤4 汉字短标签
  - threats -> 红圈 + 一句话 why
  - 底部时间轴条（t_start–t_end），t_now 高亮当前阶段
  - 图例 / 标题条（goal / model / win_condition）

配色（上级定死，禁紫、禁靛蓝）：
  底 #161A20 / 正文 #F4F7FA / 次要 #BAC4CE / 琥珀 #E8A33D；
  阶段色族：琥珀 #E8A33D、青 #3FB3B0、白 #F4F7FA、暖橙 #F08A4B。

两条出图路径共用本渲染器：LLM 成功路径（plan.json.phases）与规则兜底路径
（_fallback_plan_v2 产出同样结构），渲染器不区分来源。

imgui 内嵌预留：imgui_phase_layer(dl, plan, proj, t_now) 走最小 draw-list 协议
（add_line/add_circle/add_circle_filled/add_text/add_rect_filled），不依赖现网
代码即可用 _RecordDL 自测；真实接入点见 out/overlay/_plan_viz/integration_plan.md。

CLI：
  python -m clashlab.overlay.plan_render --plan plan.json --base base.png \
      --quad 1288,12;2314,569;1281,1193;282,562 --out roadmap.png [--t 120] \
      [--layout layout.json] [--plain] [--title "03 阵 三星"]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- 配色（禁紫/禁靛蓝）
BG = (22, 26, 32)            # #161A20 底
PANEL = (30, 37, 46)         # 面板底
INK = (244, 247, 250)        # #F4F7FA 正文
SUB = (186, 196, 206)        # #BAC4CE 次要
AMBER = (232, 163, 61)       # #E8A33D 琥珀
TEAL = (63, 179, 176)        # #3FB3B0 青
WHITE = (244, 247, 250)      # 白
WARM_ORANGE = (240, 138, 75)  # 暖橙
THREAT_RED = (229, 72, 77)   # #E5484D 威胁红
GRID = (48, 57, 69)          # 暗网格

PHASE_COLORS = [AMBER, TEAL, WHITE, WARM_ORANGE]

# ---------------------------------------------------------------- 字体（CJK 自检）
_FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
]
_FONT_CACHE: dict = {}


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    key = (size, bold)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    paths = _FONT_CANDIDATES if bold else [_FONT_CANDIDATES[1], _FONT_CANDIDATES[0],
                                           _FONT_CANDIDATES[2]]
    for p in paths:
        if os.path.exists(p):
            try:
                f = ImageFont.truetype(p, size)
                _FONT_CACHE[key] = f
                return f
            except Exception:
                continue
    f = ImageFont.load_default()
    _FONT_CACHE[key] = f
    return f


def cjk_selfcheck() -> tuple[bool, str]:
    """中文渲染自检：渲染「威胁防空」四字，统计非背景像素；为 0 即字体没出字（问号方框）。"""
    try:
        im = Image.new("RGB", (240, 60), BG)
        d = ImageDraw.Draw(im)
        d.text((10, 10), "威胁防空", font=_font(32, True), fill=INK)
        px = im.load()
        n = sum(1 for y in range(60) for x in range(240)
                if px[x, y] != BG)
        return n > 50, f"cjk_glyph_px={n}"
    except Exception as e:
        return False, f"selfcheck_error={e!r}"


# ---------------------------------------------------------------- 投影
class Projector:
    """quad 模式：tile -> 底图像素（Calib 单应）；plain 模式：tile -> 画布仿射。"""

    def __init__(self, quad=None, canvas_wh=(1200, 1000), margin=90, n=44):
        self.n = n
        self.quad = quad
        self.calib = None
        self.plain = quad is None
        if quad is not None:
            try:
                from ..geo import Calib
                self.calib = Calib.from_quad(quad, n=n)
            except Exception:
                self.plain = True
                self.calib = None
        self.canvas_wh = canvas_wh
        self.margin = margin

    def set_canvas(self, wh):
        self.canvas_wh = wh

    def __call__(self, tile):
        x, y = int(round(float(tile[0]))), int(round(float(tile[1])))
        if self.calib is not None:
            return self.calib.tile_to_px(x, y)
        W, H = self.canvas_wh
        m = self.margin
        return (m + x / self.n * (W - 2 * m), m + y / self.n * (H - 2 * m))


# ---------------------------------------------------------------- 工具
def _short(label: str, limit: int = 4) -> str:
    s = "".join(str(label or "").split())
    return s[:limit]


def _phase_color(i: int):
    return PHASE_COLORS[i % len(PHASE_COLORS)]


def phase_at_t(plan: dict, t: float):
    """当前 t 落在哪个阶段（t_start ≤ t < t_end）；越界返回最近阶段索引；无阶段返回 None。

    供 HUD 内嵌按游戏时钟高亮当前阶段。
    """
    phases = plan.get("phases") or []
    if not phases:
        return None
    for i, ph in enumerate(phases):
        try:
            a, b = float(ph.get("t_start", 0)), float(ph.get("t_end", 0))
        except (TypeError, ValueError):
            continue
        if a <= t < b:
            return i
    # t 落在所有区间外：取最近一个
    best, best_d = 0, None
    for i, ph in enumerate(phases):
        a, b = float(ph.get("t_start", 0) or 0), float(ph.get("t_end", 0) or 0)
        d = min(abs(t - a), abs(t - b))
        if best_d is None or d < best_d:
            best, best_d = i, d
    return best


def _load_layout_tiles(path: str | None) -> dict:
    """可选 layout.json：tile -> 中文短名，给 targets/threats 当标签。"""
    out = {}
    if not path or not os.path.exists(path):
        return out
    try:
        with open(path, "r", encoding="utf-8") as f:
            doc = json.load(f)
    except Exception:
        return out
    from .tactics import NAME_ZH
    zh = dict(NAME_ZH)
    zh.update(_ZH_FALLBACK)
    for b in doc.get("buildings") or []:
        tile = b.get("tile")
        if isinstance(tile, (list, tuple)) and len(tile) == 2:
            key = (int(round(tile[0])), int(round(tile[1])))
            out[key] = zh.get(b.get("type"), b.get("type") or "")
    return out


# ---------------------------------------------------------------- 建筑足迹（P2-7 路线压建筑）
# 尺寸口径：layout.json 的 tile 按「中心格」解释（geo.Calib 纯单应，0.5 格偏移已证伪）；
# 尺寸取 assets.stats(name, th=16)["size"]（TH16_OVERRIDE 已修正地狱塔/空气炮/城堡），
# STATS 无尺寸的三种按 games 实测补 DEFAULT（圣碑/喷火器/城堡 = 3×3，见 COLLAB 尺寸表）。
_DEFAULT_FOOTPRINT_SIZE = {"monolith": 3, "firespitter": 3, "clan-castle": 3}


def load_footprints(layout_path: str, quad, n: int = 44) -> list:
    """layout.json(buildings+walls) -> [{'type','tile','size','poly'}]，poly 为底图像素四边形。

    只读 layout.json，不写回；用于 P2-7 度量「路线压建筑」与渲染降透明，
    不改 plan schema，也不参与战术判定。
    """
    import json as _json

    with open(layout_path, "r", encoding="utf-8") as f:
        doc = _json.load(f)
    from ..geo import Calib
    calib = Calib.from_quad(quad, n=n)

    def _poly(tx, ty, size):
        half = float(size) / 2.0
        return [calib.tile_to_px(tx - half, ty - half),
                calib.tile_to_px(tx + half, ty - half),
                calib.tile_to_px(tx + half, ty + half),
                calib.tile_to_px(tx - half, ty + half)]

    out = []
    for b in doc.get("buildings") or []:
        tile = b.get("tile")
        typ = b.get("type")
        if not (isinstance(tile, (list, tuple)) and len(tile) == 2):
            continue
        size = _DEFAULT_FOOTPRINT_SIZE.get(typ)
        if size is None:
            try:
                from ..assets import stats
                size = stats(typ, th=16).get("size")
            except Exception:
                size = None
        size = float(size or 3)
        out.append({"type": typ, "tile": [float(tile[0]), float(tile[1])],
                    "size": size, "poly": _poly(tile[0], tile[1], size)})
    for w in doc.get("walls") or []:
        if not (isinstance(w, (list, tuple)) and len(w) == 2):
            continue
        out.append({"type": "wall", "tile": [float(w[0]), float(w[1])],
                    "size": 1.0, "poly": _poly(w[0], w[1], 1.0)})
    return out


def footprints_mask(footprints: list, size) -> Image.Image:
    """建筑足迹并集掩膜（L 模式，255=建筑/墙覆盖）。"""
    m = Image.new("L", (int(size[0]), int(size[1])), 0)
    d = ImageDraw.Draw(m)
    for fp in footprints or []:
        pts = [(float(p[0]), float(p[1])) for p in fp.get("poly") or []]
        if len(pts) >= 3:
            d.polygon(pts, fill=255)
    return m


def render_route_mask(plan: dict, size, quad, t_now: float | None = None,
                      width_scale: float = 1.0) -> Image.Image:
    """只画 phases 路线的 L 掩膜（虚线 + 末端箭头），坐标口径与 render_plan 完全一致。

    供 P2-7 度量脚本离线统计「路线像素落在建筑上的比例」，不参与 HUD/面板渲染。
    """
    W, H = int(size[0]), int(size[1])
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    proj = Projector(quad, canvas_wh=(W, H))
    active = phase_at_t(plan, t_now) if t_now is not None else None
    for i, ph in enumerate(plan.get("phases") or []):
        is_active = active == i
        width = max(1, int(round((5 if is_active else 2) * float(width_scale))))
        pts = [proj(p) for p in (ph.get("route") or [])]
        for a, b in zip(pts, pts[1:]):
            _dash_arrow(d, a, b, 255, width=width)
    return mask


# ---------------------------------------------------------------- PIL 绘制原语
def _dash_arrow(d, a, b, col, width=3, dash=14, gap=9, head=16):
    """a->b 虚线 + 末端小箭头（PIL 无原生虚线）。"""
    import math
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    dist = math.hypot(dx, dy) or 1.0
    ux, uy = dx / dist, dy / dist
    t = 0.0
    while t < dist:
        t2 = min(t + dash, dist)
        d.line([ax + ux * t, ay + uy * t, ax + ux * t2, ay + uy * t2],
               fill=col, width=width)
        t = t2 + gap
    ang = math.atan2(dy, dx)
    for s in (-0.5, 0.5):
        d.line([bx, by, bx - head * math.cos(ang - s), by - head * math.sin(ang - s)],
               fill=col, width=width)


_ZH_FALLBACK = {
    "bomb-tower": "炸弹塔",
    "firespitter": "喷火器",
    "clan-castle": "城堡",
    "monolith": "圣碑",
    "eagle-artillery": "鹰炮",
    "air-defense": "防空塔",
    "inferno-tower": "地狱塔",
    "scattershot": "散射炮",
    "archer-tower": "箭塔",
    "x-bow": "弩炮",
    "cannon": "加农炮",
    "mortar": "迫击炮",
    "air-sweeper": "空气炮",
    "spell-tower": "法术塔",
    "town-hall": "大本营",
}


def _zh_of(typ, layout_name=""):
    if layout_name:
        return layout_name
    try:
        from .tactics import NAME_ZH
        return NAME_ZH.get(typ, _ZH_FALLBACK.get(typ, typ or ""))
    except Exception:
        return _ZH_FALLBACK.get(typ, typ or "")


def _label_pill(d, x, y, text, font, fill=INK, bg=(16, 19, 24, 200)):
    tw = d.textlength(text, font=font)
    th = font.size + 6
    d.rounded_rectangle([x - 5, y - 3, x + tw + 5, y + th - 6], radius=4,
                        fill=bg)
    d.text((x, y), text, font=font, fill=fill)


def _aim_circle(d, c, r, col, label="", font=None, slot=0):
    """瞄准圈：外环 + 十字线 + 短标签；slot 决定标签方位，避免扎堆重叠。"""
    x, y = c
    d.ellipse([x - r, y - r, x + r, y + r], outline=col, width=3)
    d.line([x - r - 6, y, x - r + 2, y], fill=col, width=2)
    d.line([x + r - 2, y, x + r + 6, y], fill=col, width=2)
    d.line([x, y - r - 6, x, y - r + 2], fill=col, width=2)
    d.line([x, y + r - 2, x, y + r + 6], fill=col, width=2)
    if label and font:
        offs = [(30, -14), (-150, -14), (30, 18), (-150, 18),
                (0, -36), (0, 26), (30, -36), (-150, -36)]
        dx, dy = offs[slot % len(offs)]
        _label_pill(d, x + dx, y + dy, label, font)


def _badge(d, c, num, col, font, r=17):
    x, y = c
    d.ellipse([x - r, y - r, x + r, y + r], fill=col, outline=INK, width=2)
    tw = d.textlength(str(num), font=font)
    d.text((x - tw / 2, y - font.size / 2 - 2), str(num), font=font, fill=BG)


def _drop_marker(d, c, count, col, font):
    """投放点：菱形 + 数量标签。"""
    x, y = c
    r = 10
    d.polygon([(x, y - r), (x + r, y), (x, y + r), (x - r, y)],
              fill=col, outline=INK)
    if count and count > 1:
        d.text((x + 13, y - 9), f"×{count}", font=font, fill=INK,
               stroke_width=2, stroke_fill=BG)


# ---------------------------------------------------------------- 主渲染
def render_plan(plan: dict, base: str | None = None, quad=None,
                out_path: str | None = None, t_now: float | None = None,
                layout_tiles: dict | None = None, title: str = "",
                dim_base: float = 0.78, footprints: list | None = None,
                route_fade_alpha: int = 110) -> Image.Image:
    """渲染 v2 路线图；返回 PIL Image（同时写 out_path）。"""
    phases = plan.get("phases") or []
    threats = plan.get("threats") or []
    win = plan.get("win_condition") or ""
    layout_tiles = layout_tiles or {}

    # ---- 画布/底图
    if base and os.path.exists(base):
        im = Image.open(base).convert("RGB")
        if dim_base < 1.0:
            dark = Image.new("RGB", im.size, BG)
            im = Image.blend(dark, im, dim_base)
    else:
        im = Image.new("RGB", (1280, 1000), BG)
    W, H = im.size
    d = ImageDraw.Draw(im, "RGBA")
    proj = Projector(quad, canvas_wh=(W, H))

    fs = max(18, W // 72)          # 标签字号随画布宽
    fs_sm = max(14, W // 96)
    fs_title = max(24, W // 52)
    f_lab = _font(fs)
    f_sm = _font(fs_sm)
    f_badge = _font(fs, True)
    f_title = _font(fs_title, True)

    # ---- plain 模式暗网格；quad 模式轻画外圈
    if proj.plain:
        m = proj.margin
        for g in range(0, 45, 5):
            x = m + g / 44 * (W - 2 * m)
            y = m + g / 44 * (H - 2 * m)
            d.line([x, m, x, H - m], fill=GRID, width=1)
            d.line([m, y, W - m, y], fill=GRID, width=1)

    # ---- layout 建筑底点（可选）
    for (tx, ty), name in layout_tiles.items():
        px, py = proj([tx, ty])
        d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=(120, 132, 146, 150))

    active = phase_at_t(plan, t_now) if t_now is not None else None

    # ---- P2-7：建筑/墙足迹掩膜（只算一次）。footprints=None 时 _fa=255，
    # 路线全不透明 = 与旧实现逐像素一致（回归由 parity 断言守住）。
    f_mask_arr = None
    _fa = 255
    if footprints:
        import numpy as _np
        f_mask_arr = _np.array(footprints_mask(footprints, (W, H)), dtype=_np.uint8)
        _fa = max(0, min(255, int(route_fade_alpha)))

    # ---- phases：虚线箭头 + 圆标 + 投放点 + 目标圈（不透明度不降，当前阶段加粗）
    for i, ph in enumerate(phases):
        col = _phase_color(i)
        col_a = col + (255,)
        is_active = active == i
        route = ph.get("route") or []
        pts = [proj(p) for p in route]
        if route:
            # P2-7：本阶段路线单独成层 -> 落在建筑/墙足迹上的像素降透明后再贴回。
            # 逐阶段贴回保持旧实现的绘制顺序（后阶段路线仍覆盖前阶段标记）。
            rl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            rdraw = ImageDraw.Draw(rl)
            for a, b in zip(pts, pts[1:]):
                _dash_arrow(rdraw, a, b, col_a, width=5 if is_active else 2)
            if f_mask_arr is not None:
                ba = _np.array(rl.getchannel("A"), dtype=_np.uint8, copy=True)
                ba[f_mask_arr > 0] = _np.minimum(ba[f_mask_arr > 0], _fa)
                rl.putalpha(Image.fromarray(ba, "L"))
            im.paste(rl, (0, 0), rl)
        if pts:
            bx, by = pts[0]
            _badge(d, (bx - 30, by - 30), ph.get("i", i + 1), col_a, f_badge)
        # 投放点
        for u in ph.get("units") or []:
            dt = u.get("drop_tile")
            if dt:
                _drop_marker(d, proj(dt), int(u.get("count") or 1), col_a, f_sm)
        # 目标瞄准圈 + 短标签（slot 轮换方位避让扎堆；同名连坐去重）
        last_lab = None
        for slot, tg in enumerate(ph.get("targets") or []):
            px, py = proj(tg)
            key = (int(round(tg[0])), int(round(tg[1])))
            lab = _short(_zh_of("", layout_tiles.get(key, "")) or "")
            if lab and lab == last_lab:
                lab = ""
            last_lab = _short(_zh_of("", layout_tiles.get(key, "")) or ph.get("name", ""))
            _aim_circle(d, (px, py), 16, col_a, lab, f_lab, slot=slot)

    # ---- threats：图上只画红圈；why 收进右侧威胁清单面板，避免漂浮标注打架
    for th in threats:
        tile = th.get("tile")
        if not tile:
            continue
        px, py = proj(tile)
        d.ellipse([px - 20, py - 20, px + 20, py + 20], outline=THREAT_RED, width=3)
        d.line([px - 26, py, px - 14, py], fill=THREAT_RED, width=2)
        d.line([px + 14, py, px + 26, py], fill=THREAT_RED, width=2)

    # ---- 标题条
    goal = plan.get("goal") or ""
    model = plan.get("model") or ""
    head = f"{title or '进攻路线图'}　目标：{goal}　{model}"
    d.rectangle([0, 0, W, fs_title + 22], fill=(22, 26, 32, 220))
    d.text((18, 10), head, font=f_title, fill=INK)
    # win_condition 暂存，移到左下图例上方绘制，避免压右侧威胁面板

    # ---- 威胁清单面板（右侧）：红圆点 + 类型 + why 两行，图上红圈不挂文字
    f_panel = _font(max(13, W // 150))
    if threats:
        px0, py0 = W - 440, 68
        row_h = 46
        rows_h = row_h * len(threats) + 54
        d.rounded_rectangle([px0 - 10, py0 - 10, W - 16, py0 + rows_h], radius=6,
                            fill=(16, 19, 24, 205), outline=THREAT_RED, width=1)
        d.text((px0, py0), "威胁清单", font=f_lab, fill=THREAT_RED)
        for k, th in enumerate(threats):
            y = py0 + 34 + k * row_h
            d.ellipse([px0, y + 3, px0 + 10, y + 13], fill=THREAT_RED)
            typ = _zh_of(th.get("type", "")) or th.get("type", "")
            why = str(th.get("why") or "")[:22]
            d.text((px0 + 16, y), typ, font=f_panel, fill=INK)
            d.text((px0 + 16, y + 18), why, font=f_panel, fill=SUB)

    # ---- 图例（左下空地块，避开中央战场与底部时间轴）
    lx, ly = 24, H - 258
    if win:
        d.text((lx, ly - 46), f"胜势条件：{win[:50]}", font=f_panel, fill=SUB)
    d.rounded_rectangle([lx - 8, ly - 8, lx + 380, ly + 140], radius=6,
                        fill=(16, 19, 24, 190), outline=SUB, width=1)
    d.text((lx, ly), "图例", font=f_lab, fill=INK)
    items = [
        (AMBER, "虚线箭头=行进路线，圆内数字=阶段序号"),
        (TEAL, "瞄准圈=本阶段打击目标"),
        (THREAT_RED, "红圈=威胁（见右清单）"),
        (WHITE, "菱形=兵种投放点（×N 数量）"),
    ]
    for k, (col, txt) in enumerate(items):
        y = ly + 34 + k * 26
        d.ellipse([lx, y + 3, lx + 13, y + 16], outline=col, width=3)
        d.text((lx + 24, y), txt, font=f_panel, fill=SUB)

    # ---- 底部时间轴条
    if phases:
        ts = [float(p.get("t_start", 0) or 0) for p in phases]
        te = [float(p.get("t_end", 0) or 0) for p in phases]
        t_lo, t_hi = min(ts), max(te) or (max(ts) + 1)
        pad = 40
        bar_y = H - 74
        bar_h = 30
        span = max(t_hi - t_lo, 1.0)
        d.rounded_rectangle([pad, bar_y, W - pad, bar_y + bar_h], radius=4,
                            fill=(16, 19, 24, 210), outline=SUB, width=2)
        for i, ph in enumerate(phases):
            a = float(ph.get("t_start", 0) or 0)
            b = float(ph.get("t_end", 0) or 0)
            x0 = pad + (a - t_lo) / span * (W - 2 * pad)
            x1 = pad + (b - t_lo) / span * (W - 2 * pad)
            col = _phase_color(i)
            is_active = (active == i)
            d.rectangle([x0, bar_y, max(x1, x0 + 6), bar_y + bar_h],
                        fill=col + (235 if is_active else 140,),
                        outline=WHITE if is_active else None, width=2)
            label = f"{ph.get('i', i + 1)}.{ph.get('name', '')} {a:.0f}-{b:.0f}s"
            seg_w = x1 - x0
            if seg_w >= 70:
                lc = x0 + seg_w / 2
                tw = d.textlength(label, font=f_sm)
                d.text((lc - tw / 2, bar_y - fs_sm - 8), label, font=f_sm,
                       fill=INK if is_active else SUB)
        d.text((pad, bar_y + bar_h + 6), f"{t_lo:.0f}s", font=f_sm, fill=SUB)
        d.text((W - pad - 40, bar_y + bar_h + 6), f"{t_hi:.0f}s", font=f_sm, fill=SUB)
        if t_now is not None and t_lo <= t_now <= t_hi:
            mx = pad + (t_now - t_lo) / span * (W - 2 * pad)
            d.polygon([(mx, bar_y - 10), (mx - 8, bar_y - 20), (mx + 8, bar_y - 20)],
                      fill=WHITE)
            d.line([mx, bar_y, mx, bar_y + bar_h], fill=WHITE, width=3)
            d.text((mx + 8, bar_y - fs_sm - 26), f"t={t_now:.0f}s", font=f_sm,
                   fill=WHITE)

    if out_path:
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        im.save(out_path)
    return im


# ---------------------------------------------------------------- imgui 内嵌预留协议
def imgui_phase_layer(dl, plan: dict, proj, t_now: float | None = None,
                      scale: float = 1.0) -> None:
    """HUD 内嵌预留：最小 draw-list 协议，方法名对齐 draw.py 的 dl。

    需 dl 提供（现有 imgui draw list 已具备）：
      add_line(a, b, col, thickness)
      add_circle(center, r, col, segments, thickness)
      add_circle_filled(center, r, col)
      add_text(pos, col, text)
      add_rect_filled(a, b, col)
    col 为 (r,g,b,a) 0..1 四元组；proj(tile)->(x,y) 屏幕坐标。
    不调用任何现网模块，可用 _RecordDL 离线自测。
    """
    phases = plan.get("phases") or []
    active = phase_at_t(plan, t_now) if t_now is not None else None
    for i, ph in enumerate(phases):
        col = _phase_color(i)
        col1 = tuple(c / 255.0 for c in col) + (1.0 if active is None or active == i else 0.35,)
        route = ph.get("route") or []
        pts = [proj(p) for p in route]
        for a, b in zip(pts, pts[1:]):
            dl.add_line(a, b, col1, 2.5 * scale)
        if pts:
            dl.add_circle_filled(pts[0], 15 * scale, col1)
            dl.add_text((pts[0][0] - 5, pts[0][1] - 7), (0.1, 0.1, 0.12, 1.0),
                         str(ph.get("i", i + 1)))
        for u in ph.get("units") or []:
            if u.get("drop_tile"):
                dl.add_circle_filled(proj(u["drop_tile"]), 8 * scale, col1)
        for tg in ph.get("targets") or []:
            dl.add_circle(proj(tg), 14 * scale, col1, 24, 2.0 * scale)
    for th in plan.get("threats") or []:
        if th.get("tile"):
            dl.add_circle(proj(th["tile"]), 18 * scale,
                          tuple(c / 255.0 for c in THREAT_RED) + (1.0,), 24, 2.5 * scale)


class _RecordDL:
    """离线自测用：记录调用，不画图。"""
    def __init__(self):
        self.calls = []

    def add_line(self, a, b, col, thickness=1.0):
        self.calls.append(("line", a, b, col, thickness))

    def add_circle(self, c, r, col, segments=24, thickness=1.0):
        self.calls.append(("circle", c, r, col, segments, thickness))

    def add_circle_filled(self, c, r, col):
        self.calls.append(("circle_filled", c, r, col))

    def add_text(self, pos, col, text):
        self.calls.append(("text", pos, col, text))

    def add_rect_filled(self, a, b, col):
        self.calls.append(("rect", a, b, col))


def _selfcheck_imgui(plan: dict) -> bool:
    dl = _RecordDL()
    imgui_phase_layer(dl, plan, lambda t: (float(t[0]) * 20, float(t[1]) * 20),
                      t_now=40)
    kinds = {c[0] for c in dl.calls}
    return {"line", "circle", "circle_filled"} <= kinds and len(dl.calls) > 3


# ---------------------------------------------------------------- CLI
def _parse_quad(s: str | None):
    if not s:
        return None
    pts = []
    for chunk in s.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        xy = chunk.split(",")
        if len(xy) != 2:
            continue
        pts.append([float(xy[0]), float(xy[1])])
    return pts if len(pts) == 4 else None


def main(argv=None):
    ap = argparse.ArgumentParser(description="v2 战术路线图离屏渲染")
    ap.add_argument("--plan", required=True, help="plan.json 路径")
    ap.add_argument("--base", default="", help="底图 PNG（省略则 plain 暗色网格）")
    ap.add_argument("--quad", default="", help="四角 x,y;x,y;x,y;x,y（上右下左）")
    ap.add_argument("--out", required=True, help="输出 PNG 路径")
    ap.add_argument("--t", type=float, default=None, help="当前秒数，高亮阶段")
    ap.add_argument("--layout", default="", help="可选 layout.json，补建筑短标签")
    ap.add_argument("--title", default="", help="标题条文字")
    ap.add_argument("--plain", action="store_true", help="强制 plain 网格，不用 quad")
    args = ap.parse_args(argv)

    with open(args.plan, "r", encoding="utf-8") as f:
        plan = json.load(f)
    ok, detail = cjk_selfcheck()
    print(f"[selfcheck] cjk {detail} ok={ok}")
    if not ok:
        print("[selfcheck] 警告：中文字体未出字，标签可能变方框", file=sys.stderr)

    quad = None if args.plain else _parse_quad(args.quad)
    tiles = _load_layout_tiles(args.layout or None)
    im = render_plan(plan, base=args.base or None, quad=quad, out_path=args.out,
                     t_now=args.t, layout_tiles=tiles, title=args.title)
    # imgui 预留接口离线自测
    ok2 = _selfcheck_imgui(plan)
    print(f"[selfcheck] imgui_layer_calls ok={ok2}")
    print(f"[render] {args.out} {im.size} phases={len(plan.get('phases') or [])} "
          f"threats={len(plan.get('threats') or [])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
