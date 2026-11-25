# -*- coding: utf-8 -*-
# 事故恢复：被覆盖的 b15/b16/b17 新帧改名 b30/b31/b32；从旧 base 画布重建原行0三帧
import json, os, cv2, numpy as np, shutil
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BLK=os.path.join(ROOT,"out","overlay","blocks3")
LOG=os.path.join(BLK,"collect_log.json")
log=json.load(open(LOG,encoding="utf-8"))

# 1) 追加的三条（index15,16,17）当前文件名叫 b15/b16/b17，实为北扩新帧 → 改名 b30/b31/b32
ren={"b15.png":"b30.png","b16.png":"b31.png","b17.png":"b32.png"}
for t in log["tiles"][15:]:
    if t["file"] in ren:
        dst=ren[t["file"]]
        shutil.move(os.path.join(BLK,t["file"]),os.path.join(BLK,dst))
        t["file"]=dst
log["last"]="b32.png"

# 2) 从旧拼接画布重建原 row0 三帧（place.py 平移后：b17@0,0 b16@440,0 b15@880,0，各905x550）
base=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_stitched_base.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
H=550; W=905
for name,cx in [("b17.png",0),("b16.png",440),("b15.png",880)]:
    crop=base[0:H,cx:cx+W].copy()
    cv2.imencode(".png",crop)[1].tofile(os.path.join(BLK,name))
    print("rebuilt",name,crop.shape)

json.dump(log,open(LOG,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print("log entries:",len(log["tiles"]))
for i,t in enumerate(log["tiles"]): print(i,t["file"],t["dx"],t["dy"])
