# -*- coding: utf-8 -*-
"""把「大本营偏心 / 对空 / 对地」三项干净指标变成战术文案（简报 / LLM 提示 / 面板）。
Turns three reliable findings (TH bias / air / ground coverage) into tactical text."""
from __future__ import annotations

from . import layout_score

_DIR_ZH = {"north": "北", "south": "南", "east": "东", "west": "西"}
_SEV_ORDER = {"critical": 0, "weak": 1, "info": 2}


def _th_finding(layout, metrics):
    th = next((b for b in (layout.get("buildings") or []) if b.get("type") == "town-hall"), None)
    if th is None:
        return None
    m = next((x for x in metrics if x["id"] == "town-hall-protection"), None)
    c = float((m or {}).get("details", {}).get("centrality", 1.0) or 0.0)
    # 阈值：<0.85 视为「偏」（0.85≈距中心不到 1/6 对角线）；>=0.85 只给 info 级别，不报弱点
    _sev = "critical" if c < 0.55 else ("weak" if c < 0.85 else "info")
    grid = int(layout.get("grid", layout_score.GRID_DEFAULT))
    d = layout_score.direction_of(layout_score.building_center(th),
                                  (grid / 2.0, grid / 2.0))
    side = _DIR_ZH.get(d, d)
    if _sev == "info":
        text = "大本营较居中（中心度 %.2f，偏%s侧不明显）→ 任意方向切入都要多破一层。" % (c, side)
    else:
        text = ("大本营偏%s侧（中心度 %.2f）→ 从他侧切入可少破一层墙，正面留双投石/冰冻"
                " 清集结；三星路线优先选大本营远侧。" % (side, c))
    return {"key": "town-hall-protection",
            "severity": _sev,
            "text": text,
            "detail": {"centrality": round(c, 3), "side": d}}


def _coverage_finding(layout, metrics, mid, layer, label):
    m = next((x for x in metrics if x["id"] == mid), None)
    if m is None:
        return None
    score = float(m.get("score", 100.0))
    # 战术角度：只要没满覆盖就给出（<90 weak，<100 info），0 直接 critical
    if score >= 100.0:
        return None
    kw = {("want_air" if layer == "air" else "want_ground"): True}
    try:
        buckets = layout_score.coverage_by_direction(layout, **kw)
    except Exception:
        buckets = {}
    weak_sides = [ _DIR_ZH.get(d, d) for d, b in (buckets or {}).items()
                   if b.get("total", 0) >= 2 and b["covered"] / float(b["total"]) < 0.5 ]
    side_txt = ("；弱侧 %s" % "、".join(weak_sides)) if weak_sides else ""
    if score <= 0.0:
        text = "没有任何%s覆盖（0%%）→ %s路线全开，可直接全压。" % (label, "空军" if layer == "air" else "陆军")
    else:
        text = "%s覆盖 %.0f%%%s → %s优先走弱侧，主攻前用一发法术清该侧%s。" % (
            label, score, side_txt,
            "空军" if layer == "air" else "陆军",
            "防空" if layer == "air" else "对地火力")
    sev = "critical" if score <= 0.0 else ("weak" if score < 90.0 else "info")
    return {"key": mid,
            "severity": sev,
            "text": text,
            "detail": {"score": round(score, 1), "weak_sides": weak_sides}}


def findings(layout):
    """layout dict -> 弱点条目（只含三项干净指标）；无布局返回 []。"""
    if not isinstance(layout, dict) or not (layout.get("buildings") or []):
        return []
    try:
        r = layout_score.score_layout(layout)
    except Exception:
        return []
    metrics = r.get("metrics") or []
    out = [_th_finding(layout, metrics),
           _coverage_finding(layout, metrics, "air-coverage", "air", "对空"),
           _coverage_finding(layout, metrics, "ground-coverage", "ground", "对地")]
    out = [x for x in out if x]
    out.sort(key=lambda f: _SEV_ORDER.get(f["severity"], 3))
    return out


def summary_line(fs):
    """单行摘要（日志/面板/简报首行）。"""
    if not fs:
        return ""
    heads = []
    for f in fs[:3]:
        if f["key"] == "town-hall-protection":
            heads.append("大本营偏%s" % _DIR_ZH.get(f.get("detail", {}).get("side", ""), "?"))
        elif f["key"] == "air-coverage":
            heads.append("对空 %.0f%%" % float(f.get("detail", {}).get("score", 0)))
        elif f["key"] == "ground-coverage":
            heads.append("对地 %.0f%%" % float(f.get("detail", {}).get("score", 0)))
    return "布局弱点：" + " · ".join(heads)


def prompt_block(obj):
    """给 LLM 的文本块：接受 findings 列表或含 defense_findings 的 prebattle dict。"""
    if isinstance(obj, dict):
        fs = obj.get("defense_findings") or []
    else:
        fs = obj or []
    if not fs:
        return ""
    lines = ["【布局弱点（本地可算，供战术复核参考）】"]
    for f in fs[:3]:
        lines.append("- " + str(f.get("text", "")))
    return "\n".join(lines)
