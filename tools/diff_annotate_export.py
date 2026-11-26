# -*- coding: utf-8 -*-
import json, os
SRC = r"C:\Users\Admin（无密码）\Downloads\clash_annotate_2026-11-26071640.json"
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
d = json.load(open(SRC, encoding="utf-8"))
print("keys:", list(d.keys()), "| schema:", d.get("schema"), "| exported:", d.get("exported_at"))
print("bases:", len(d.get("bases") or []))
cur = {}
for i in range(1, 7):
    bid = "%02d" % i
    p = os.path.join(BASE, "out", "annotate", bid + "_annotated.json")
    if os.path.exists(p):
        cur[bid] = json.load(open(p, encoding="utf-8"))
for b in d.get("bases") or []:
    bid = b.get("id")
    new_bs = b.get("buildings") or []
    old_bs = (cur.get(bid) or {}).get("buildings") or []
    def key(x): return (str(x.get("type")), int(x["tile"][0]), int(x["tile"][1]))
    oldk = {key(x): x for x in old_bs}
    newk = {key(x): x for x in new_bs}
    added = [x for k, x in newk.items() if k not in oldk]
    removed = [x for k, x in oldk.items() if k not in newk]
    lv_changed = []
    for k, x in newk.items():
        if k in oldk and (oldk[k].get("level") or None) != (x.get("level") or None):
            lv_changed.append((oldk[k].get("level"), x.get("level"), x.get("type"), x.get("tile")))
    print("%s: old=%d new=%d added=%d removed=%d level_changed=%d" % (
        bid, len(old_bs), len(new_bs), len(added), len(removed), len(lv_changed)))
    for x in added[:6]:
        print("   +", x)
    for x in removed[:6]:
        print("   -", x)
