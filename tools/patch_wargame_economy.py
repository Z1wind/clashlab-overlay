# -*- coding: utf-8 -*-
"""wargame：未知/经济类建筑按非防御处理（dps=0），尺寸查 ruleset。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "wargame.py")
t = open(p, encoding="utf-8").read()

if "_ruleset_size" in t:
    print("already patched")
else:
    helper = (
        "def _ruleset_size(btype, default=3):\n"
        "    \"\"\"从 knowledge/th_ruleset.json 查建筑占地（reviewed）。\"\"\"\n"
        "    try:\n"
        "        import json as _json\n"
        "        import os as _os\n"
        "        _p = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),\n"
        "                           \"knowledge\", \"th_ruleset.json\")\n"
        "        if not getattr(_ruleset_size, \"_cache\", None):\n"
        "            _ruleset_size._cache = _json.load(open(_p, encoding=\"utf-8\")).get(\"objects\") or {}\n"
        "        o = _ruleset_size._cache.get(str(btype)) or {}\n"
        "        w = int(o.get(\"width\") or 0)\n"
        "        h = int(o.get(\"height\") or 0)\n"
        "        return max(w, h) or default\n"
        "    except Exception:\n"
        "        return default\n"
        "\n"
        "\n"
        "def _is_defense_type(btype):\n"
        "    \"\"\"只有 assets.STATS / TH16_OVERRIDE 里的类型算防御；经济/兵营/陷阱按非防御。\"\"\"\n"
        "    try:\n"
        "        from . import assets as _assets\n"
        "        return (str(btype) in _assets.STATS) or (str(btype) in getattr(_assets, \"TH16_OVERRIDE\", {}))\n"
        "    except Exception:\n"
        "        return False\n"
        "\n"
        "\n"
    )
    anchor = "def parse_layout(data):"
    if anchor in t:
        t = t.replace(anchor, helper + anchor, 1)
    else:
        print("parse_layout anchor miss")
    old = ("        st = building_stats(typ)\n"
           "        size = int(raw.get(\"size\") or st[\"size\"] or 3)")
    new = ("        st = building_stats(typ)\n"
           "        if not _is_defense_type(typ):\n"
           "            # 经济/兵营等非防御建筑：不参与火力，HP 用通用低值，尺寸查 ruleset\n"
           "            st = {\"hp\": 1000.0, \"dps\": 0.0, \"range\": 0.0, \"size\": _ruleset_size(typ)}\n"
           "        size = int(raw.get(\"size\") or st[\"size\"] or 3)")
    if old in t:
        t = t.replace(old, new, 1)
    else:
        print("size anchor miss")
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("wargame economy patch done")
