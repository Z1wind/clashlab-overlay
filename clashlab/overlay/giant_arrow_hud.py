# -*- coding: utf-8 -*-
"""HUD 图层：把穿云箭（from->to + 被穿目标）直接画在游戏画面上。

数据来源：config/giant_arrow_overlay.json（tools/giant_arrow_cli.py --emit-overlay 生成）。
坐标只走 calib.tile_to_px，与其它 HUD 标记同一口径。
"""
from __future__ import annotations

import json
import math
import os

from . import draw as _d

_CACHE = {"key": None, "plan": None}

# 颜色（RGB 0-255，画的时候统一走 draw._col）
RED = (232, 74, 74)          # 防空火箭
ORANGE = (242, 162, 60)      # 吹风机
GREY = (150, 150, 150)       # 特斯拉（隐身，仅提示）
TEAL = (80, 190, 180)        # 其它防御
ARROW = (242, 182, 60)
LABEL = (255, 216, 128)


def overlay_plan_path(root):
    return os.path.join(root, "config", "giant_arrow_overlay.json")


def load_overlay_plan(root):
    """读 config/giant_arrow_overlay.json（按 mtime 缓存）；不存在返回 None。"""
    path = overlay_plan_path(root)
    try:
        mtime = os.stat(path).st_mtime
    except OSError:
        return None
    key = (path, mtime)
    if _CACHE.get("key") == key:
        return _CACHE.get("plan")
    try:
        with open(path, "r", encoding="utf-8") as f:
            plan = json.load(f)
    except Exception:
        return None
    _CACHE["key"] = key
    _CACHE["plan"] = plan
    return plan


def hit_color(typ):
    if typ == "air-defense":
        return RED
    if typ == "air-sweeper":
        return ORANGE
    if typ == "hidden-tesla":
        return GREY
    return TEAL


def draw_giant_arrow(dl, calib, plan, win_w=1280.0, win_h=720.0, tip_label=True):
    """在 imgui drawlist 上画实线箭 + 编号命中圈；返回画出的命中数。"""
    if calib is None or not isinstance(plan, dict):
        return 0
    try:
        frm = plan.get("from") or []
        to = plan.get("to") or []
        ax, ay = calib.tile_to_px(float(frm[0]), float(frm[1]))
        bx, by = calib.tile_to_px(float(to[0]), float(to[1]))
    except Exception:
        return 0
    sx, sy = win_w / 1280.0, win_h / 720.0
    ax, ay, bx, by = ax * sx, ay * sy, bx * sx, by * sy

    dl.add_line(_d.imgui_pt(ax, ay), _d.imgui_pt(bx, by), _d._col((*ARROW, 0.25)), 7.0)
    dl.add_line(_d.imgui_pt(ax, ay), _d.imgui_pt(bx, by), _d._col((*ARROW, 0.95)), 2.6)
    ang = math.atan2(by - ay, bx - ax)
    s = 14.0
    dl.add_triangle_filled(
        _d.imgui_pt(bx, by),
        _d.imgui_pt(bx - s * math.cos(ang - 0.42), by - s * math.sin(ang - 0.42)),
        _d.imgui_pt(bx - s * math.cos(ang + 0.42), by - s * math.sin(ang + 0.42)),
        _d._col((*ARROW, 0.95)))
    dl.add_circle(_d.imgui_pt(ax, ay), 7.0, _d._col((*ARROW, 0.95)), 0, 2.2)
    if tip_label:
        dl.add_text(_d.imgui_pt(ax + 10.0, ay - 8.0), _d._col((*LABEL, 1.0)), "穿云箭")

    n = 0
    for i, h in enumerate(plan.get("hits") or []):
        tile = h.get("tile")
        if not (isinstance(tile, (list, tuple)) and len(tile) == 2):
            continue
        try:
            x, y = calib.tile_to_px(float(tile[0]), float(tile[1]))
        except Exception:
            continue
        x, y = x * sx, y * sy
        rgb = hit_color(h.get("type"))
        dl.add_circle_filled(_d.imgui_pt(x, y), 13.0, _d._col((*rgb, 0.30)))
        dl.add_circle(_d.imgui_pt(x, y), 13.0, _d._col((*rgb, 0.95)), 0, 2.2)
        num = "?" if h.get("type") == "hidden-tesla" else str(h.get("order", i + 1))
        tw = 8.0 * len(num)  # 数字宽度近似，避免测试/无 imgui 上下文时崩溃
        dl.add_text(_d.imgui_pt(x - tw / 2.0, y - 7.0), _d._col((255, 255, 255, 1.0)), num)
        n += 1
    return n
