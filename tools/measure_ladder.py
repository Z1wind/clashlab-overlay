# -*- coding: utf-8 -*-
# 离线量已落盘的 ladder 帧：edge_step / fft_texture / blob，输出表
import sys, os, cv2, numpy as np, json
sys.path.insert(0, r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\tools")
from v6_tile_px import measure_tile_px
D = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\ladder"
for fn in sorted(os.listdir(D)):
    if not fn.startswith("zoom_") or not fn.endswith(".png"): continue
    img = cv2.imdecode(np.fromfile(os.path.join(D,fn),dtype=np.uint8), cv2.IMREAD_COLOR)
    r = measure_tile_px(img)
    print(fn, "est=",r["estimate"], "cons=",r["consensus"], "crit=",r["criteria"], "warn=",r["warning"])
