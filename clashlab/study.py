# -*- coding: utf-8 -*-
"""研究视图：把防御覆盖、弱侧与候选方案画成一张可读的报告图（俯视网格，不做透视）。"""
import os

import numpy as np
from PIL import Image, ImageDraw

from . import analysis, assets
from .render import font, YELLOW, ORANGE, GREEN, BLUE, WHITE, GREY

CELL = 10
PAD = 18

TYPE_COLOR = {
    "town-hall": (214, 176, 96),
    "eagle-artillery": (226, 122, 56),
    "scattershot": (206, 96, 120),
    "inferno-tower": (200, 80, 80),
    "x-bow": (150, 120, 220),
    "air-defense": (96, 180, 200),
    "wizard-tower": (120, 150, 230),
    "archer-tower": (120, 200, 140),
    "cannon": (170, 180, 190),
    "mortar": (160, 150, 130),
    "air-sweeper": (110, 170, 190),
    "hidden-tesla": (140, 140, 200),
    "bomb-tower": (190, 150, 110),
    "spell-tower": (150, 200, 210),
    "defense": (140, 146, 152),
}

GRID_W = 44 * CELL


def _grid_origin(panel_x):
    return panel_x + PAD + 30, PAD + 66


def _cell_xy(origin, x, y):
    ox, oy = origin
    return ox + x * CELL, oy + y * CELL


def _panel(d, x0, y0, w, h, title, sub=""):
    d.rectangle([x0, y0, x0 + w, y0 + h], fill=(15, 19, 23), outline=(52, 60, 66))
    d.text((x0 + 12, y0 + 10), title, font=font(16, True), fill=WHITE)
    if sub:
        d.text((x0 + 12, y0 + 30), sub, font=font(11), fill=GREY)


def _draw_grid(d, origin, n, color=(46, 54, 60)):
    ox, oy = origin
    for i in range(n + 1):
        d.line([ox + i * CELL, oy, ox + i * CELL, oy + n * CELL], fill=color, width=1)
        d.line([ox, oy + i * CELL, ox + n * CELL, oy + i * CELL], fill=color, width=1)
    for i in range(0, n + 1, 4):
        d.text((ox + i * CELL - 5, oy - 14), str(i), font=font(9), fill=(120, 130, 136))
        d.text((ox - 16, oy + i * CELL - 5), str(i), font=font(9), fill=(120, 130, 136))


def _layout_panel(d, sim, report, origin):
    n = sim.n
    _draw_grid(d, origin, n)
    # 防御覆盖范围
    for b in sim.buildings:
        r = b.get("range") or 0
        if r <= 0:
            continue
        cx, cy = _cell_xy(origin, b["tile"][0], b["tile"][1])
        rp = int(r * CELL)
        col = (200, 90, 80, 60) if b["dps"] >= 250 else (120, 170, 210, 48)
        d.ellipse([cx - rp, cy - rp, cx + rp, cy + rp], outline=col[:3] + (170,), width=1)
    # 建筑
    for b in sim.buildings:
        st = assets.STATS.get(b["type"], {})
        k = st.get("size", 3)
        x, y = b["tile"]
        ox, oy = _cell_xy(origin, x - k / 2.0, y - k / 2.0)
        col = TYPE_COLOR.get(b["type"], TYPE_COLOR["defense"])
        d.rectangle([ox, oy, ox + k * CELL, oy + k * CELL], fill=col + (235,), outline=(12, 16, 20))
        if b["type"] == "town-hall":
            d.text((ox - 6, oy - 14), "大本营", font=font(10), fill=YELLOW)
    # 最外露目标
    for e in report["exposed"][:3]:
        ox, oy = _cell_xy(origin, e["tile"][0], e["tile"][1])
        d.ellipse([ox - 5, oy - 5, ox + 5, oy + 5], outline=(255, 170, 60), width=2)


def _cover_panel(d, sim, report, origin):
    n = sim.n
    _draw_grid(d, origin, n)
    cover = analysis.coverage_map(sim)
    vmax = max(float(cover.max()), 1.0)
    for x in range(n):
        for y in range(n):
            v = float(cover[x, y]) / vmax
            if v <= 0.02:
                continue
            col = (int(30 + 215 * v), int(90 + 40 * (1 - v)), int(200 * (1 - v) + 40))
            ox, oy = _cell_xy(origin, x, y)
            d.rectangle([ox + 1, oy + 1, ox + CELL - 1, oy + CELL - 1], fill=col + (int(60 + 150 * v),))
    # 弱侧标点
    for b in report["blind"][:2]:
        ox, oy = _cell_xy(origin, b["tile"][0], b["tile"][1])
        d.ellipse([ox - 4, oy - 4, ox + 4, oy + 4], fill=GREEN)
    # 重心
    cx, cy = report["centroid"]
    ox, oy = _cell_xy(origin, cx, cy)
    d.line([ox - 10, oy, ox + 10, oy], fill=WHITE, width=2)
    d.line([ox, oy - 10, ox, oy + 10], fill=WHITE, width=2)


def _entries_panel(d, sim, plans, origin):
    n = sim.n
    _draw_grid(d, origin, n)
    for b in sim.buildings:
        st = assets.STATS.get(b["type"], {})
        k = st.get("size", 3)
        ox, oy = _cell_xy(origin, b["tile"][0] - k / 2.0, b["tile"][1] - k / 2.0)
        col = TYPE_COLOR.get(b["type"], TYPE_COLOR["defense"])
        d.rectangle([ox, oy, ox + k * CELL, oy + k * CELL], fill=col + (120,))
    pal = {"A": GREEN, "B": YELLOW, "C": BLUE}
    c = n / 2.0
    for pl in plans:
        col = pal.get(pl["id"], GREEN)
        for e in pl["entries"]:
            ox, oy = _cell_xy(origin, e["tile"][0], e["tile"][1])
            d.ellipse([ox - 6, oy - 6, ox + 6, oy + 6], fill=col, outline=(10, 20, 14))
            d.text((ox + 8, oy - 6), f"{pl['id']}{e['troops']}", font=font(10, True), fill=col)
        # 主线路径
        path = pl.get("path", {}).get("path") or []
        if len(path) > 1:
            pts = [_cell_xy(origin, p[0] + 0.5, p[1] + 0.5) for p in path[::3]]
            d.line(pts, fill=col + (200,), width=2)
        # 核心
    ox, oy = _cell_xy(origin, c, c)
    d.ellipse([ox - 8, oy - 8, ox + 8, oy + 8], outline=ORANGE, width=2)


def render_study(sim, report, plans, path, title="部落冲突阵型研究"):
    W, H = 1560, 1006
    img = Image.new("RGBA", (W, H), (10, 13, 16, 255))
    d = ImageDraw.Draw(img)

    d.text((PAD, 12), title, font=font(20, True), fill=WHITE)
    d.text((PAD, 38), "俯视 44×44 网格　·　格号为棋盘坐标　·　圆圈为该防御射程　·　橙圈为外露高价值目标",
           font=font(11), fill=GREY)

    pw, ph, gap = 470, 514, 12
    y0 = 96
    xs = [12, 12 + pw + gap, 12 + 2 * (pw + gap)]
    _panel(d, xs[0], y0, pw, ph, "阵型与防御射程", f"{len(sim.buildings)} 个建筑")
    _panel(d, xs[1], y0, pw, ph, "覆盖热图与盲区", f"核心覆盖 {report['core_cover_dps']} dps")
    _panel(d, xs[2], y0, pw, ph, "候选撒兵点与路线", "A 单点强攻 / B 双线 / C 弱侧")

    _layout_panel(d, sim, report, _grid_origin(xs[0] + 30))
    _cover_panel(d, sim, report, _grid_origin(xs[1] + 30))
    _entries_panel(d, sim, plans, _grid_origin(xs[2] + 30))

    # 下方文字区：左列研究结论，右列候选方案
    ty = y0 + ph + 18
    colw = 740
    d.text((PAD, ty), "研究结论", font=font(15, True), fill=WHITE)
    ty += 26
    for note in report["notes"][:7]:
        d.text((PAD, ty), "·", font=font(11), fill=GREEN)
        lines = _wrap(note, 52)
        d.multiline_text((PAD + 12, ty), "\n".join(lines), font=font(11), fill=(206, 212, 218), spacing=4)
        ty += 15 * len(lines) + 6

    tx = PAD + colw + 20
    ty2 = y0 + ph + 18
    d.text((tx, ty2), "候选方案（相对排序，非真实破坏率）", font=font(15, True), fill=WHITE)
    ty2 += 26
    for pl in plans:
        color = {"A": GREEN, "B": YELLOW, "C": BLUE}.get(pl["id"], WHITE)
        d.text((tx, ty2), f"{pl['id']} {pl['name']}　预测 {pl['predicted']:.2f}　风险 {pl['risk']}　"
                          f"路径 {pl['path']['steps']} 格 / {pl['path']['time_s']}s",
               font=font(12, True), fill=color)
        ty2 += 19
        lines = _wrap(pl["rationale"], 60)
        d.multiline_text((tx + 14, ty2), "\n".join(lines), font=font(10), fill=(190, 198, 206), spacing=3)
        ty2 += 13 * len(lines) + 10

    # 底部口径说明：相对排序，非真实破坏率；写明归一化口径，避免误导
    d.text((PAD, H - 26),
           "口径：predicted 为同批方案原始热图均值按"
           "「最优=1.0」归一的相对排序，非真实破坏率；risk 为同批相对暴露口径，"
           "均只用于横向比较候选方案。",
           font=font(10), fill=(140, 150, 158))

    img.convert("RGB").save(path)
    return path


def _wrap(text, width):
    out, line = [], ""
    for ch in text:
        line += ch
        if len(line) >= width:
            out.append(line)
            line = ""
    if line:
        out.append(line)
    return out


def build_study(sim, army, ring=None, out_dir="out/study"):
    ring = ring if ring is not None else analysis.deployment_ring(sim)
    report = analysis.defense_report(sim, ring, army)
    plans = analysis.candidate_plans(sim, ring, army, report)
    os.makedirs(out_dir, exist_ok=True)
    p = render_study(sim, report, plans, os.path.join(out_dir, "study.png"))
    return report, plans, p


def _ring(n=44, inset=1):
    m = np.zeros((n + 1, n + 1), np.uint8)
    m[inset:n + 1 - inset, inset:n + 1 - inset] = 1
    ring = m.copy()
    ring[inset + 4:n + 1 - inset - 4, inset + 4:n + 1 - inset - 4] = 0
    return ring
