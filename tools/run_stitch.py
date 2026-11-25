# -*- coding: utf-8 -*-
# run_stitch.py — 按 collect_log.json 实测累积偏移喂 v6_stitch，出整阵+报告
import json, os, cv2, numpy as np, sys
sys.path.insert(0,r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\tools")
from v6_stitch import stitch
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BLK=os.path.join(ROOT,"out","overlay","blocks")
log=json.load(open(os.path.join(BLK,"collect_log.json"),encoding="utf-8"))
tiles=[]; offsets=[]
for t in log["tiles"]:
    im=cv2.imdecode(np.fromfile(os.path.join(BLK,t["file"]),dtype=np.uint8),cv2.IMREAD_COLOR)
    tiles.append(im); offsets.append((t["cx"],t["cy"]))
# 平移到非负
minx=min(o[0] for o in offsets); miny=min(o[1] for o in offsets)
offsets=[(o[0]-minx,o[1]-miny) for o in offsets]
canvas,report=stitch(tiles,offsets=offsets,overlap=0.2,
                     report_path=os.path.join(BLK,"stitch_report.json"))
out=os.path.join(ROOT,"out","overlay","v6_stitched_base.png")
cv2.imencode(".png",canvas)[1].tofile(out)
print("all_pass=",report["all_pass"])
for t in report["tiles"]:
    print(t["index"],t["file"] if "file" in t else "",f"seam={t['seam_err_px']} pass={t['pass']}")
print("canvas",canvas.shape)
