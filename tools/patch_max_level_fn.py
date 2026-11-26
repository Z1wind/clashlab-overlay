# -*- coding: utf-8 -*-
"""修 max_level_of：优先用 reviewed ruleset 的逐 TH max_levels。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "levels.py")
t = open(p, encoding="utf-8").read()
old = '''def max_level_of(name, th=None, default=DEFAULT_MAX_LEVEL):
    """取某建筑在某 TH 的 reviewed 最高等级；查不到回 default。"""
    try:
        from . import th_data
        st = th_data.stats(name, th or 16)
        lv = int(st.get("level") or 0)
        return lv or default
    except Exception:
        return default'''
new = '''def max_level_of(name, th=None, default=DEFAULT_MAX_LEVEL):
    """取某建筑在某 TH 的 reviewed 最高等级（优先 knowledge/th_ruleset.json）。

    顺序：ruleset.objects[name].max_levels[str(th)] -> th_data.stats().level -> default。
    """
    th = int(th or 16)
    try:
        import json
        import os
        _p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "knowledge", "th_ruleset.json")
        rs = json.load(open(_p, encoding="utf-8"))
        obj = (rs.get("objects") or {}).get(str(name)) or {}
        lv = int((obj.get("max_levels") or {}).get(str(th)) or 0)
        if lv > 0:
            return lv
    except Exception:
        pass
    try:
        from . import th_data
        st = th_data.stats(name, th)
        lv = int(st.get("level") or 0)
        return lv or default
    except Exception:
        return default'''
if old in t:
    t = t.replace(old, new)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("max_level_of patched")
else:
    print("anchor miss")
