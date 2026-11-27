# -*- coding: utf-8 -*-
import os, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "out", "layouts_src")
os.makedirs(OUT, exist_ok=True)
URLS = {
  "war_138": "https://clashofclans-layouts.com/pics/th16_plans/war/original/th16_war_138.jpg",
  "war_143": "https://clashofclans-layouts.com/pics/th16_plans/war/original/th16_war_143.jpg",
  "war_141": "https://clashofclans-layouts.com/pics/th16_plans/war/original/th16_war_141.jpg",
  "war_139": "https://clashofclans-layouts.com/pics/th16_plans/war/original/th16_war_139.jpg",
  "defence_17": "https://clashofclans-layouts.com/pics/th16_plans/defence/original/th16_defence_17.jpg",
}
for name, u in URLS.items():
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=90) as r:
            data = r.read()
        dst = os.path.join(OUT, name + ".jpg")
        open(dst, "wb").write(data)
        im = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        print(name, len(data), "bytes", None if im is None else im.shape)
    except Exception as e:
        print(name, "FAIL", str(e)[:100])
