# -*- coding: utf-8 -*-
"""把 layout.json 渲染成 2D 俯视阵型图（PNG），并可导出 2D 交换 JSON。

思路：识别/标注给出的 44×44 tile 布局 → 2D 化（俯视图 + 图例），
便于人工核对、方案分享、以及喂给 2D 布局引擎（格式参考 clash-blueprint-engine 的 save format，MIT）。
"""
from __future__ import annotations

import json
import os

import numpy as np

try:
    import cv2
except Exception:  # pragma: no cover
    cv2 = None

GRID = 44
# 注意：cv2 是 BGR 序
CATEGORY_COLOR = {
    "town-hall": (0, 200, 255),      # 琥珀金
    "trap": (80, 80, 215),           # 绯红
    "defense": (235, 150, 70),       # 钢蓝
    "economy": (60, 200, 255),       # 暖金（矿/采集器/仓库）
    "storage": (90, 200, 120),       # 薄荷绿
    "army": (200, 210, 120),         # 沙金
    "other": (160, 160, 160),        # 灰
}
DEFENSE_TYPES = {"cannon", "archer-tower", "mortar", "air-defense", "wizard-tower", "bomb-tower",
                 "hidden-tesla", "air-sweeper", "x-bow", "inferno-tower", "scattershot", "monolith",
                 "spell-tower", "multi-archer-tower", "ricochet-cannon", "firespitter", "eagle-artillery"}
STORAGE_TYPES = {"gold-storage", "elixir-storage", "dark-elixir-storage"}
ARMY_TYPES = {"barracks", "dark-barracks", "army-camp", "laboratory", "spell-factory", "dark-spell-factory",
              "clan-castle", "builder-hut", "builders-hut"}
ECONOMY_TYPES = {"gold-mine", "elixir-collector", "dark-elixir-drill", "gold-storage",
                 "elixir-storage", "dark-elixir-storage"}
TRAP_TYPES = {"bomb", "spring-trap", "air-bomb", "giant-bomb", "seeking-air-mine",
              "tornado-trap", "skeleton-trap", "giga-bomb"}
EXTRA_ARMY = {"hero-hall", "pet-house", "blacksmith", "workshop", "helper-hut", "bobs-hut"}
SIZE_HINT = {
    "town-hall": 4, "eagle-artillery": 3, "scattershot": 3, "inferno-tower": 2, "monolith": 3,
    "hidden-tesla": 2, "air-sweeper": 2, "spell-tower": 2, "clan-castle": 3,
}


def _size(t):
    if t in SIZE_HINT:
        return SIZE_HINT[t]
    if t in ("cannon", "archer-tower", "wizard-tower", "bomb-tower", "x-bow", "multi-archer-tower",
             "ricochet-cannon", "firespitter", "mortar", "air-defense"):
        return 3
    return 3


def _category(t):
    if t == "town-hall":
        return "town-hall"
    if t in TRAP_TYPES:
        return "trap"
    if t in DEFENSE_TYPES:
        return "defense"
    if t in ECONOMY_TYPES:
        return "economy"
    if t in STORAGE_TYPES:
        return "storage"
    if t in ARMY_TYPES or t in EXTRA_ARMY:
        return "army"
    return "other"


# ---------------------------------------------------------------- 美化绘制
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
    margin, hud_h, legend_h = 26, 54, 40
    w = g * cell + margin * 2
    h = g * cell + margin + hud_h + legend_h
    img = _bg_gradient(h, w, top=(30, 22, 18), bottom=(46, 36, 28))
    # 外框 + 内底板
    _rounded_rect(img, 2, 2, w - 3, h - 3, 16, (58, 70, 86), 2)
    # 图例带
    _rounded_rect(img, margin - 6, margin + hud_h - 6, w - margin + 6, margin + hud_h + g * cell + 6, 12, (22, 28, 36), -1)
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
        if bw >= 3 * cell:
            short = tp.replace("-", " ")[:8]
            (tw_, th_), _ = cv2.getTextSize(short, cv2.FONT_HERSHEY_SIMPLEX, 0.32, 1)
            _text_outline(img, short, (bx + (bw - tw_) // 2, by + bw // 2 + 4), 0.32, (245, 248, 252))
    # 标题栏
    _rounded_rect(img, margin, 12, w - margin, 12 + hud_h - 16, 10, (16, 21, 28), -1)
    cv2.line(img, (margin + 10, 30), (margin + 26, 30), (61, 163, 232), 3, cv2.LINE_AA)
    _text_outline(img, "ClashLab  ·  2D top-down", (margin + 34, 36), 0.52, (243, 247, 251))
    _text_outline(img, "grid %d  annotated %d  walls %d  (未标注建筑不会显示)" % (g, len(buildings), len(walls)),
                  (margin + 300, 36), 0.42, (170, 186, 204))
    # 图例（cv2 不渲染中文，用英文；底部独立带，不压地图）
    lx, ly = margin + 10, h - 16
    cv2.line(img, (margin + 6, ly - 24), (w - margin - 6, ly - 24), (48, 58, 72), 1, cv2.LINE_AA)
    for label, ckey in (("Town Hall", "town-hall"), ("Trap", "trap"), ("Defense", "defense"),
                        ("Economy", "economy"), ("Storage", "storage"), ("Army", "army"),
                        ("Other", "other")):
        col = CATEGORY_COLOR[ckey]
        _rounded_rect(img, lx, ly - 12, lx + 14, ly + 2, 3, col, -1)
        _text_outline(img, label, (lx + 20, ly), 0.40, (205, 216, 230))
        lx += 92
    cv2.imencode(".png", img)[1].tofile(out_png)
    return img.shape[1], img.shape[0], len(buildings), len(walls)


def export_2d_json(layout, out_json):
    """导出 2D 交换格式（tile 坐标 + 类别），便于喂给 2D 布局引擎。"""
    g = int(layout.get("grid", GRID))
    objs = []
    for b in layout.get("buildings") or []:
        t = str(b.get("type") or "")
        objs.append({"type": t, "category": _category(t), "tile": list(b.get("tile") or [0, 0]),
                     "size": _size(t)})
    doc = {"schema": "clashlab-2d-v1", "grid": {"width": g, "height": g},
           "objects": objs, "walls": [list(map(int, w)) for w in (layout.get("walls") or [])]}
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    return doc
