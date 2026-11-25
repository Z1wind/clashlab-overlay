# -*- coding: utf-8 -*-
# v15_stitch_max.py — 调用 v6_stitch 拼 max 块，行优先左->右。新文件。
import os, sys, cv2, numpy as np, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v6_stitch import stitch
R = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\_recon"
M = os.path.join(R,"max")
tiles=[]; order=[]
for r in range(9):
    for c in range(6):
        p=os.path.join(M,f"b_c{c}r{r}.png")
        im=cv2.imdecode(np.fromfile(p,dtype=np.uint8),1)
        tiles.append(im); order.append(f"c{c}r{r}")
canvas,report=stitch(tiles, overlap=0.5, grid=(9,6),
                     report_path=os.path.join(R,"stitch_max_report.json"))
cv2.imencode(".png",canvas)[1].tofile(os.path.join(R,"recon_full_max_raw.png"))
print("canvas",canvas.shape,"all_pass",report["all_pass"])
worst=0;worst_i=None
for t in report["tiles"]:
    if t["seam_err_px"] and t["seam_err_px"]>worst:
        worst=t["seam_err_px"];worst_i=t["index"]
print("worst seam",worst,"at",order[worst_i] if worst_i is not None else None)
fails=[order[t["index"]] for t in report["tiles"] if not t["pass"]]
print("fail:",fails)
