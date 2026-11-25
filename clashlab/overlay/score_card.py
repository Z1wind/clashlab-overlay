# -*- coding: utf-8 -*-
"""评分 → PANEL 文案（纯函数、可单测；带指纹缓存）。
Defense score -> panel text (pure functions, fingerprint-cached)."""
from __future__ import annotations

from .. import layout_score

_CACHE = {"key": None, "card": None}
EMPTY = {"available": False, "overall": 0.0, "grade": "-", "top": [],
         "status": "", "bottom": ""}


def _fingerprint(layout):
    try:
        b = layout.get("buildings") or []
        w = layout.get("walls") or []
        first_b = (b[0].get("type"), tuple(b[0].get("tile") or ())) if b else ("", ())
        return (layout.get("grid"), len(b), len(w), first_b)
    except Exception:
        return None


def card_from_layout(layout):
    """layout dict -> card dict（available/overall/grade/top/status/bottom）。"""
    if not isinstance(layout, dict) or not (layout.get("buildings") or []):
        return dict(EMPTY)
    fp = _fingerprint(layout)
    if fp is not None and _CACHE.get("key") == fp and _CACHE.get("card"):
        return _CACHE["card"]
    try:
        r = layout_score.score_layout(layout)
    except Exception:
        return dict(EMPTY)
    top = [str(w.get("message", "")) for w in (r.get("weakPoints") or [])[:2] if w.get("message")]
    card = {
        "available": True,
        "overall": float(r.get("overall", 0.0)),
        "grade": str(r.get("grade", "-")),
        "top": top,
        "status": " · 评分 %.1f %s" % (float(r.get("overall", 0.0)), r.get("grade", "-")),
        "bottom": "防御评分 %.1f %s · %s" % (
            float(r.get("overall", 0.0)), r.get("grade", "-"),
            (top[0] if top else "无重大弱点")),
    }
    _CACHE.update({"key": fp, "card": card})
    return card


def detail_lines(layout, max_lines=2):
    """研究页/阵型页底部显示的两行明细：大本营偏心、对空/对地覆盖。"""
    if not isinstance(layout, dict) or not (layout.get("buildings") or []):
        return []
    try:
        from .. import defense_findings as _df
        fs = _df.findings(layout)
    except Exception:
        return []
    out = []
    for f in fs:
        t = str(f.get("text", ""))
        if not t:
            continue
        out.append("弱点：" + t)
        if len(out) >= max_lines:
            break
    return out


def status_suffix(card):
    return card.get("status", "") if isinstance(card, dict) and card.get("available") else ""


def bottom_text(card):
    return card.get("bottom", "") if isinstance(card, dict) and card.get("available") else ""


def reset_cache():
    _CACHE.update({"key": None, "card": None})
