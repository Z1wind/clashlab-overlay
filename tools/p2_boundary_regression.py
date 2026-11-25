# -*- coding: utf-8 -*-
"""回归验证：正常（基地完整可见）帧仍应 usable；贴边帧必须不可用。"""
import os, sys, json
import numpy as np, cv2
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab import vision

frames = [
    ("recon_median", os.path.join(BASE, "out", "overlay", "_recon", "recon_median.png")),
    ("zoom1_fullbase", os.path.join(BASE, "out", "overlay", "_auto_label", "zoom1.png")),
    ("printwindow_live", os.path.join(BASE, "out", "overlay", "_p2", "printwindow_frame.png")),
]
out = []
for name, p in frames:
    if not os.path.exists(p):
        out.append({"frame": name, "error": "missing"}); continue
    img = cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)
    calib, meta = vision.detect_boundary(img)
    assess = vision.boundary_assessment(calib, meta)
    out.append({"frame": name, "shape": list(img.shape[:2]), "source": meta.get("source"),
                "confidence": round(float(meta.get("confidence", 0)), 3),
                "clipped": meta.get("clipped"), "usable": assess.get("usable"),
                "reason": assess.get("usable_reason")})
    print(name, "conf=%.3f" % meta.get("confidence", 0), "clipped=", meta.get("clipped"), "usable=", assess.get("usable"))
json.dump(out, open(os.path.join(BASE, "out", "overlay", "_p2", "boundary_regression.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
