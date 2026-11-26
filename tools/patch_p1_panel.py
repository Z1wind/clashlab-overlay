# -*- coding: utf-8 -*-
"""面板加「建筑构成」行。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "overlay", "pages.py")
t = open(p, encoding="utf-8").read()

helper = '''

_BUILDINGS_CACHE = {"key": None, "line": ""}


def _fmt_buildings_counts(counts):
    """把分类计数压成一行文案（纯函数，便于测试）。"""
    if not counts or not counts.get("total"):
        return "建筑：无数据"
    parts = []
    for key, label in (("defense", "防御"), ("economy", "经济"), ("army", "兵营"),
                       ("trap", "陷阱"), ("storage", "仓库"), ("other", "其它")):
        n = int(counts.get(key) or 0)
        if n:
            parts.append("%s %d" % (label, n))
    line = "建筑：" + " · ".join(parts)
    if counts.get("walls"):
        line += " · 墙 %d" % int(counts["walls"])
    if counts.get("maxed_pct") is not None:
        line += " · 满级 %d%%" % int(counts["maxed_pct"])
    return line


def _count_buildings(layout):
    """按分类统计当前布局（防御/经济/兵营/陷阱/仓库/其它/墙/满级占比）。"""
    out = {"total": 0, "defense": 0, "economy": 0, "army": 0, "trap": 0,
           "storage": 0, "other": 0, "walls": 0, "maxed_pct": None}
    if not isinstance(layout, dict):
        return out
    try:
        import re as _re
        from .. import levels as _levels
        from ..topdown import _category
    except Exception:
        return out
    bs = layout.get("buildings") or []
    out["walls"] = len(layout.get("walls") or [])
    m = _re.search(r"th(\\d{1,2})", str(layout.get("name") or ""), _re.I)
    th = int(m.group(1)) if m else 16
    maxed = 0
    for b in bs:
        t = str(b.get("type") or "")
        cat = _category(t)
        out[cat if cat in out else "other"] += 1
        out["total"] += 1
        lv = b.get("level")
        if lv:
            try:
                if int(lv) >= int(_levels.max_level_of(t, th, strict=True) or 0):
                    maxed += 1
            except Exception:
                pass
    if out["total"]:
        out["maxed_pct"] = round(100.0 * maxed / out["total"])
    return out


def _buildings_line(state):
    """研究页建筑构成行（按 layout 指纹缓存，热路径不重算）。"""
    try:
        layout = getattr(state, "layout", None)
        if not isinstance(layout, dict):
            return "建筑：无数据"
        key = (layout.get("name"), len(layout.get("buildings") or []), len(layout.get("walls") or []))
        if _BUILDINGS_CACHE.get("key") == key:
            return _BUILDINGS_CACHE.get("line") or "建筑：无数据"
        line = _fmt_buildings_counts(_count_buildings(layout))
        _BUILDINGS_CACHE.update({"key": key, "line": line})
        return line
    except Exception:
        return "建筑：无数据"

'''
if "_fmt_buildings_counts" not in t:
    t = t.replace("def _sim_line(state):", helper + "def _sim_line(state):", 1)
    old = '''    imgui.text_colored(imgui.ImVec4(*SUBTLE), _strategy_line(state))
    y += 20.0'''
    new = '''    imgui.text_colored(imgui.ImVec4(*SUBTLE), _strategy_line(state))
    y += 20.0
    imgui.text_colored(imgui.ImVec4(*SUBTLE), _buildings_line(state))
    y += 20.0'''
    if old in t:
        t = t.replace(old, new, 1)
        open(p, "w", encoding="utf-8", newline="\n").write(t)
        print("pages patched")
    else:
        print("draw anchor miss")
else:
    print("already patched")
