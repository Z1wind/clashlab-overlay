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
CATEGORY_COLOR = {
    "town-hall": (255, 215, 0),
    "defense": (70, 130, 220),
    "storage": (60, 180, 75),
    "army": (180, 160, 60),
    "other": (160, 160, 160),
}
DEFENSE_TYPES = {"cannon", "archer-tower", "mortar", "air-defense", "wizard-tower", "bomb-tower",
                 "hidden-tesla", "air-sweeper", "x-bow", "inferno-tower", "scattershot", "monolith",
                 "spell-tower", "multi-archer-tower", "ricochet-cannon", "firespitter", "eagle-artillery"}
STORAGE_TYPES = {"gold-storage", "elixir-storage", "dark-elixir-storage"}
ARMY_TYPES = {"barracks", "dark-barracks", "army-camp", "laboratory", "spell-factory", "dark-spell-factory",
              "clan-castle", "builder-hut", "builders-hut"}
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
    if t in DEFENSE_TYPES:
        return "defense"
    if t in STORAGE_TYPES:
        return "storage"
    if t in ARMY_TYPES:
        return "army"
    return "other"


def render_topdown(layout, out_png, cell=24, grid=None):
    """layout dict -> 2D 俯视 PNG。返回 (w, h, n_buildings, n_walls)。"""
    if cv2 is None:
        raise RuntimeError("opencv required")
    g = int(grid or layout.get("grid", GRID))
    img = np.full((g * cell, g * cell, 3), 245, np.uint8)
    for i in range(g + 1):
        cv2.line(img, (0, i * cell), (g * cell, i * cell), (225, 225, 225), 1)
        cv2.line(img, (i * cell, 0), (i * cell, g * cell), (225, 225, 225), 1)
    walls = layout.get("walls") or []
    for x, y in walls:
        if 0 <= int(x) < g and 0 <= int(y) < g:
            cv2.rectangle(img, (int(x) * cell, int(y) * cell),
                          ((int(x) + 1) * cell - 1, (int(y) + 1) * cell - 1), (120, 120, 120), -1)
    buildings = layout.get("buildings") or []
    for b in buildings:
        t = str(b.get("type") or "")
        x, y = b.get("tile") or (0, 0)
        k = _size(t)
        x0 = (int(x) - (k - 1) // 2) * cell
        y0 = (int(y) - (k - 1) // 2) * cell
        col = CATEGORY_COLOR[_category(t)]
        cv2.rectangle(img, (x0 + 2, y0 + 2), (x0 + k * cell - 3, y0 + k * cell - 3), col, -1)
        cv2.rectangle(img, (x0 + 2, y0 + 2), (x0 + k * cell - 3, y0 + k * cell - 3), (40, 40, 40), 1)
        short = t.replace("-", " ")[:6]
        cv2.putText(img, short, (x0 + 4, y0 + cell + 2), cv2.FONT_HERSHEY_SIMPLEX, 0.34, (20, 20, 20), 1)
    cv2.putText(img, "ClashLab top-down  grid=%d  buildings=%d  walls=%d" % (g, len(buildings), len(walls)),
                (8, g * cell - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (60, 60, 60), 1)
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
