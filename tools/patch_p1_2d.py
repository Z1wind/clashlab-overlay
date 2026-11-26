# -*- coding: utf-8 -*-
"""P1：2D 图分类/图例扩展 + topdown_cli 支持 annotated + 面板建筑行。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"

# ---------- 1) topdown.py ----------
p = os.path.join(BASE, "clashlab", "topdown.py")
t = open(p, encoding="utf-8").read()
old_colors = '''CATEGORY_COLOR = {
    "town-hall": (0, 200, 255),      # 琥珀金
    "defense": (235, 150, 70),       # 钢蓝
    "storage": (90, 200, 120),       # 薄荷绿
    "army": (200, 210, 120),         # 沙金
    "other": (160, 160, 160),        # 灰
}'''
new_colors = '''CATEGORY_COLOR = {
    "town-hall": (0, 200, 255),      # 琥珀金
    "trap": (80, 80, 215),           # 绯红
    "defense": (235, 150, 70),       # 钢蓝
    "economy": (60, 200, 255),       # 暖金（矿/采集器/仓库）
    "storage": (90, 200, 120),       # 薄荷绿
    "army": (200, 210, 120),         # 沙金
    "other": (160, 160, 160),        # 灰
}'''
if old_colors in t:
    t = t.replace(old_colors, new_colors)
    print("colors extended")
CONSTS = '''ECONOMY_TYPES = {"gold-mine", "elixir-collector", "dark-elixir-drill", "gold-storage",
                  "elixir-storage", "dark-elixir-storage"}
TRAP_TYPES = {"bomb", "spring-trap", "air-bomb", "giant-bomb", "seeking-air-mine",
              "tornado-trap", "skeleton-trap", "giga-bomb", "bomb-tower"?''',
# 用普通字符串更安全：直接插常量 + 改 _category
if "ECONOMY_TYPES" not in t:
    t = t.replace('SIZE_HINT = {', '''ECONOMY_TYPES = {"gold-mine", "elixir-collector", "dark-elixir-drill", "gold-storage",
                 "elixir-storage", "dark-elixir-storage"}
TRAP_TYPES = {"bomb", "spring-trap", "air-bomb", "giant-bomb", "seeking-air-mine",
              "tornado-trap", "skeleton-trap", "giga-bomb"}
EXTRA_ARMY = {"hero-hall", "pet-house", "blacksmith", "workshop", "helper-hut", "bobs-hut"}
SIZE_HINT = {''', 1)
old_cat = '''def _category(t):
    if t == "town-hall":
        return "town-hall"
    if t in DEFENSE_TYPES:
        return "defense"
    if t in STORAGE_TYPES:
        return "storage"
    if t in ARMY_TYPES:
        return "army"
    return "other"'''
new_cat = '''def _category(t):
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
    return "other"'''
if old_cat in t:
    t = t.replace(old_cat, new_cat)
    print("category extended")
old_legend = '''    for label, ckey in (("Town Hall", "town-hall"), ("Defense", "defense"), ("Storage", "storage"),
                        ("Army", "army"), ("Other", "other")):'''
new_legend = '''    for label, ckey in (("Town Hall", "town-hall"), ("Trap", "trap"), ("Defense", "defense"),
                        ("Economy", "economy"), ("Storage", "storage"), ("Army", "army"),
                        ("Other", "other")):'''
if old_legend in t:
    t = t.replace(old_legend, new_legend)
    t = t.replace("        lx += 104", "        lx += 92")
    print("legend extended")
open(p, "w", encoding="utf-8", newline="\n").write(t)

# ---------- 2) topdown_cli.py ----------
p2 = os.path.join(BASE, "clashlab", "topdown_cli.py")
t2 = open(p2, encoding="utf-8").read()
t2 = t2.replace('    ap.add_argument("--layout", required=True)',
                '    ap.add_argument("--layout", default=None)\n'
                '    ap.add_argument("--annotated", default=None, help="标注文件（out/annotate/NN_annotated.json）")')
t2 = t2.replace('    import json\n    lay = json.load(open(a.layout, encoding="utf-8"))',
                '    import json\n'
                '    src = a.annotated or a.layout\n'
                '    if not src:\n'
                '        raise SystemExit("需要 --layout 或 --annotated")\n'
                '    lay = json.load(open(src, encoding="utf-8"))')
t2 = t2.replace('    name = os.path.splitext(os.path.basename(a.layout))[0]\n'
                '    parent = os.path.basename(os.path.dirname(os.path.abspath(a.layout)))',
                '    name = os.path.splitext(os.path.basename(src))[0]\n'
                '    parent = os.path.basename(os.path.dirname(os.path.abspath(src)))')
open(p2, "w", encoding="utf-8", newline="\n").write(t2)
print("topdown_cli patched")
