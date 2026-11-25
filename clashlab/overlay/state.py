# -*- coding: utf-8 -*-
"""OverlayState：覆盖层运行时状态容器 + mtime 热重载。

契约字段（对外不变）：root / marks / quad_px / render_size / study_png /
study_brief / study_info / candidates_png / candidates / farm / layout /
mode / page / live。缺文件一律降级，不抛异常。
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# 实测 quad（1280x720 渲染坐标系）：[[697,107],[944,351],[672,585],[347,327]]
DEFAULT_QUAD = [[697, 107], [944, 351], [672, 585], [347, 327]]
RENDER_SIZE = (1280, 720)
# v9-②：归一化 quad（0–1，相对客户区宽/高），与像素解耦；换视口由构造层还原
DEFAULT_QUAD_NORM = [[p[0] / RENDER_SIZE[0], p[1] / RENDER_SIZE[1]] for p in DEFAULT_QUAD]


@dataclass
class OverlayState:
    root: str
    marks: dict = field(default_factory=dict)
    quad_px: list = field(default_factory=lambda: [list(p) for p in DEFAULT_QUAD])
    # v9-②：归一化 quad（0–1）；缺省由 DEFAULT_QUAD / 1280x720 派生，旧像素 quad
    # 载入时按 1280x720 基准反推归一化（兼容 layout_candidates.json 旧产物）
    quad_norm: list = field(default_factory=lambda: [list(p) for p in DEFAULT_QUAD_NORM])
    render_size: tuple = RENDER_SIZE
    study_png: Path | None = None
    study_brief: str = ""
    study_info: dict = field(default_factory=dict)
    candidates_png: Path | None = None
    candidates: list = field(default_factory=list)
    farm: dict = field(default_factory=dict)
    layout: dict | None = None
    mode: str = "HUD"
    page: str = "research"
    live: bool = False


def _read_json(path: str, default: Any):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _read_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def _exists(path: str) -> bool:
    return bool(path) and os.path.exists(path)


def _candidates_from(raw: dict) -> list:
    out = []
    for row in raw.get("candidates") or []:
        if not isinstance(row, dict):
            continue
        bbox = row.get("bbox") or row.get("box")
        if not (isinstance(bbox, (list, tuple)) and len(bbox) == 4):
            continue
        try:
            bbox = [float(v) for v in bbox]
        except (TypeError, ValueError):
            continue
        conf = row.get("confidence", row.get("score", 0.0))
        try:
            conf = float(conf)
        except (TypeError, ValueError):
            conf = 0.0
        out.append({
            "id": str(row.get("id") or row.get("label") or "c"),
            "label": str(row.get("label") or row.get("type") or "未命名"),
            "bbox": bbox,
            "confidence": max(0.0, min(1.0, conf)),
        })
    return out


def _fill(state: OverlayState) -> None:
    root = state.root
    # marks.json
    state.marks = _read_json(os.path.join(root, "out", "marks", "marks.json"), {}) or {}
    # 研究包
    sp = Path(root) / "out" / "study" / "study.png"
    state.study_png = sp if _exists(str(sp)) else None
    state.study_brief = _read_text(os.path.join(root, "out", "prebattle", "brief.md"))
    state.study_info = _read_json(os.path.join(root, "out", "prebattle", "info.json"), {}) or {}
    # 候选
    cand_raw = _read_json(os.path.join(root, "out", "overlay", "layout_candidates.json"), {}) or {}
    state.candidates = _candidates_from(cand_raw)
    if cand_raw.get("quad"):
        state.quad_px = [[float(p[0]), float(p[1])] for p in cand_raw["quad"]]
        # v9-②：旧表是 1280x720 基准绝对像素，反推归一化供视口适配
        state.quad_norm = [[float(p[0]) / RENDER_SIZE[0], float(p[1]) / RENDER_SIZE[1]]
                           for p in state.quad_px]
    cp = Path(root) / "out" / "overlay" / "overlay.png"
    state.candidates_png = cp if _exists(str(cp)) else None
    # farm 报告（只读）
    state.farm = _read_json(os.path.join(root, "out", "farm", "farm_report.json"), {}) or {}
    # 冻结 layout
    lay = _read_json(os.path.join(root, "layouts", "layout_current.json"), None)
    state.layout = lay if isinstance(lay, dict) else None


def load_state(root: str) -> OverlayState:
    state = OverlayState(root=os.path.abspath(root))
    _fill(state)
    return state


def reload(state: OverlayState) -> None:
    """按 mtime 侦测后的全量重读；缺文件降级，不抛。"""
    try:
        _fill(state)
    except Exception:
        # 热重载失败保留旧态，不崩主线程
        pass
