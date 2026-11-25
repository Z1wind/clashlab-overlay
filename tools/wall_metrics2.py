# -*- coding: utf-8 -*-
import os, json
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
d = json.load(open(os.path.join(BASE, "out", "overlay", "_p3b", "walls_extracted", "_metrics.json"), encoding="utf-8"))
for b in ("02", "04", "05"):
    v = d["bases"][b]
    print("==", b, "kind", v["meta"]["homography"].get("kind"))
    print("   counts:", json.dumps(v.get("counts"), ensure_ascii=False))
    m = v["metrics"]
    for tag in ("old", "new", "closed_variant"):
        if tag in m:
            x = m[tag]
            print("   %-14s walls=%-4s iso%%=%.1f ring=%.2f comps=%d dead=%d" % (
                tag, x.get("wall_count"), 100 * x.get("isolated_ratio", 0),
                x.get("th_ring_coverage", 0), x.get("compartment_count", 0), x.get("dead_zone_count", 0)))
    print("   metrics keys:", list(m.keys()))
