# -*- coding: utf-8 -*-
"""下载 clashofclans-layouts.com 的 TH16 阵图（对应已标注的 5 个阵）。"""
import os, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "out", "layouts_src")
os.makedirs(OUT, exist_ok=True)
CAND = {
  "war_138": ["https://clashofclans-layouts.com/pics/th16_plans/war/th16_war_138.jpg",
              "https://clashofclans-layouts.com/pics/th16_plans/war/preview/th16_war_138.jpg"],
  "war_143": ["https://clashofclans-layouts.com/pics/th16_plans/war/th16_war_143.jpg"],
  "war_141": ["https://clashofclans-layouts.com/pics/th16_plans/war/th16_war_141.jpg"],
  "war_139": ["https://clashofclans-layouts.com/pics/th16_plans/war/th16_war_139.jpg"],
  "defence_17": ["https://clashofclans-layouts.com/pics/th16_plans/defence/th16_defence_17.jpg"],
}
for name, urls in CAND.items():
    dst = os.path.join(OUT, name + ".jpg")
    ok = False
    for u in urls:
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as r:
                data = r.read()
            if len(data) < 10000:
                continue
            open(dst, "wb").write(data)
            im = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
            print(name, "OK", len(data), "bytes", None if im is None else im.shape)
            ok = True
            break
        except Exception as e:
            print(name, "try fail", str(e)[:80])
    if not ok:
        print(name, "FAILED")
