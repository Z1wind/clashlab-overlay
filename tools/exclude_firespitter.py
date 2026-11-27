# -*- coding: utf-8 -*-
"""训练数据统一排除「喷火器(firespitter)」：用户已说明其标注为误标。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "build_synth_level_dataset.py")
t = open(p, encoding="utf-8").read()
if "EXCLUDE_TYPES" not in t:
    # 在 imports 之后插入常量
    lines = t.splitlines()
    out, inserted = [], False
    for ln in lines:
        out.append(ln)
        if not inserted and ln.startswith("import ") and "os" in ln:
            out.append("")
            out.append('EXCLUDE_TYPES = {"firespitter"}  # 用户明确：误标，训练忽略')
            inserted = True
    t = "\n".join(out) + "\n"
    # 类型过滤
    t = t.replace('    for ck_name in types:',
                  '    for ck_name in types:\n        if ck_name in EXCLUDE_TYPES:\n            continue', 1)
    # 兜底：label 写出后过滤
    t = t.replace('    print("[synth] samples:", len(arr)',
                  '    labels = [l for l in labels if l.get("type") not in EXCLUDE_TYPES]\n    print("[synth] samples:", len(arr)', 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("exclude patched in build_synth_level_dataset.py")
else:
    print("already patched")
