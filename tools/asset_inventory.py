# -*- coding: utf-8 -*-
# asset_inventory.py — 盘点 assets/coc/buildings 全部模板，写 tpl_inventory.json（只读素材）
import json, os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
MAN = os.path.join(ROOT, "assets", "coc", "buildings", "manifest_buildings.json")
m = json.load(open(MAN, encoding="utf-8"))
inv = []
for e in m["entries"]:
    p = os.path.join(ROOT, e["file"].replace("/", os.sep))
    im = cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    alpha_frac = float((im[:, :, 3] > 40).mean()) if im.ndim == 3 and im.shape[2] == 4 else 0.0
    inv.append({
        "file": e["file"], "type": e["type"], "level": e["level"],
        "px_w": int(e["px_w"]), "px_h": int(e["px_h"]),
        "w_tiles": e["w_tiles"], "h_tiles": e["h_tiles"],
        "alpha_frac": round(alpha_frac, 4),
        "native_px_per_tile": round(e["px_w"] / e["w_tiles"], 1) if e["w_tiles"] else None,
    })
out = os.path.join(ROOT, "out", "recog", "tpl_inventory.json")
os.makedirs(os.path.dirname(out), exist_ok=True)
json.dump({"count": len(inv), "entries": inv}, open(out, "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
by = {}
for r in inv:
    by.setdefault(r["type"], []).append(r["level"])
print("total", len(inv))
for k, v in sorted(by.items()):
    print(k, len(v), "levels", min(v), "-", max(v))
