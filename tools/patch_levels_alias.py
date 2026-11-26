# -*- coding: utf-8 -*-
"""levels: alias + strict；apply_max_levels: 严格模式（查不到就跳过）。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"

p = os.path.join(BASE, "clashlab", "levels.py")
t = open(p, encoding="utf-8").read()
if "ALIASES" not in t:
    t = t.replace("DEFAULT_MAX_LEVEL = 20", "DEFAULT_MAX_LEVEL = 20\n# 标注工具/旧布局里的别名 -> ruleset 规范名\nALIASES = {\n    \"builder-hut\": \"builders-hut\",\n    \"builder-huts\": \"builders-hut\",\n    \"dark-spell-factory\": \"dark-spell-factory\",\n    \"seeking-air-mine\": \"seeking-air-mine\",\n}")
    old = 'def max_level_of(name, th=None, default=DEFAULT_MAX_LEVEL):'
    new = 'def max_level_of(name, th=None, default=DEFAULT_MAX_LEVEL, strict=False):'
    t = t.replace(old, new, 1)
    t = t.replace('''    th = int(th or 16)
    try:
        import json
        import os''', '''    th = int(th or 16)
    name = ALIASES.get(str(name), str(name))
    try:
        import json
        import os''', 1)
    t = t.replace('''    try:
        from . import th_data
        st = th_data.stats(name, th)
        lv = int(st.get("level") or 0)
        return lv or default
    except Exception:
        return default''', '''    try:
        from . import th_data
        st = th_data.stats(name, th)
        lv = int(st.get("level") or 0)
        if lv > 0:
            return lv
    except Exception:
        pass
    return None if strict else default''')
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("levels patched")

p2 = os.path.join(BASE, "tools", "apply_max_levels.py")
t2 = open(p2, encoding="utf-8").read()
t2 = t2.replace('''        max_lv = levels.max_level_of(t, th)''',
'''        max_lv = levels.max_level_of(t, th, strict=True)
        if max_lv is None:
            rows.append({"type": t, "tile": b.get("tile"), "level": None, "skipped": "unknown-type"})
            continue''')
open(p2, "w", encoding="utf-8", newline="\n").write(t2)
print("apply_max_levels patched")
