# -*- coding: utf-8 -*-
import os, json
import numpy as np, cv2
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
s = json.load(open(os.path.join(BASE, "out", "overlay", "_quad_calib", "summary.json"), encoding="utf-8"))
for b in ("03", "05", "06"):
    e = s.get(b, {})
    img = cv2.imdecode(np.fromfile(os.path.join(BASE, "bases", "th16", b, "base.png"), np.uint8), cv2.IMREAD_COLOR)
    lay = json.load(open(os.path.join(BASE, "bases", "th16", b, "layout.json"), encoding="utf-8"))
    print(b, "img", img.shape[1], "x", img.shape[0], "grid", lay.get("grid"), "quad", e.get("quad"))
