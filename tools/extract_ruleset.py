# -*- coding: utf-8 -*-
"""从 vendored base-validator reviewed ruleset 提取 TH1–19 数据 -> knowledge/th_ruleset.json。"""
import glob, json, os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
f = sorted(glob.glob(os.path.join(BASE, "out", "overlay", "_p3a", "upstream",
                                  "clash-of-clans-base-validator-main", "rulesets", "home-*.json")))[-1]
d = json.load(open(f, encoding="utf-8"))

def kebab(n):
    return n.replace("_", "-")

objs = {}
for name, o in (d.get("objects") or {}).items():
    objs[kebab(name)] = {"width": int(o.get("width") or 0), "height": int(o.get("height") or 0),
                         "category": o.get("category"),
                         "max_levels": {str(k): int(v) for k, v in (o.get("max_levels") or {}).items()},
                         "status": o.get("status"), "sources": o.get("sources") or []}

ths = {}
for th, t in (d.get("town_halls") or {}).items():
    lim = {kebab(k): int(v) for k, v in (t.get("limits") or {}).items()}
    unlocked = sorted([k for k, v in lim.items() if v > 0])
    ths[str(th)] = {"limits": lim, "unlocked": unlocked}

mergers = {}
for name, m in (d.get("mergers") or {}).items():
    mergers[kebab(name)] = {"consumes": {kebab(k): int(v) for k, v in (m.get("consumes") or {}).items()},
                            "ingredient_level": int(m.get("ingredient_level") or 0)}

out = {"schema_version": 1, "source": "Peter537/clash-of-clans-base-validator ruleset (MIT), vendored copy",
       "ruleset_id": d.get("id"), "verified_on": d.get("verified_on"), "review_status": d.get("review_status"),
       "grid": 44, "town_hall_size": 4, "objects": objs, "town_halls": ths, "mergers": mergers}
p = os.path.join(BASE, "knowledge", "th_ruleset.json")
os.makedirs(os.path.dirname(p), exist_ok=True)
json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", p, os.path.getsize(p), "B | objects:", len(objs), "| THs:", len(ths))
print("TH19 unlocked sample:", ths["19"]["unlocked"][:14])
print("eagle size:", objs.get("eagle-artillery", {}).get("width"), "| spiky-tower:", objs.get("spiky-tower", {}).get("width"))
print("air-defense max_levels:", {k: objs["air-defense"]["max_levels"].get(k) for k in ("13","16","17","18","19")})
