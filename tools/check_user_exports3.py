# -*- coding: utf-8 -*-
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DL = os.path.join(os.path.expanduser("~"), "Downloads")
for i in range(1, 9):
    f = "annot_b%02d.json" % i
    p = os.path.join(DL, f)
    if not os.path.exists(p):
        print(f, "MISSING"); continue
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception as e:
        print(f, "BAD JSON", e); continue
    b = d.get("buildings") or []
    cn = d.get("corners_norm") or []
    tiles = [x.get("tile") or [] for x in b]
    xs = [t[0] for t in tiles if len(t) >= 2]; ys = [t[1] for t in tiles if len(t) >= 2]
    print(f, "ver", d.get("version"), "| image", d.get("image"), "| size", d.get("image_size"),
          "| corners", len(cn), "| bld", len(b), "| types", len(set(x.get("type") for x in b)),
          "| x", (min(xs), max(xs)) if xs else None, "y", (min(ys), max(ys)) if ys else None)
