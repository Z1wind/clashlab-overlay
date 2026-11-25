# -*- coding: utf-8 -*-
# 最终三图：base裁净 / grid(仿射格网) / marks(候选标注,未核验灰显)
import cv2, numpy as np, os, json
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT=os.path.join(ROOT,"out","overlay","l0new")
base=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_l0_two_shot_base.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
H,W=base.shape[:2]
# 裁净右侧UI(x>1060相对裁口 -> 原x>905)
base_trim=base[:,:905].copy()
cv2.imencode(".png",base_trim)[1].tofile(os.path.join(ROOT,"out","overlay","v6_l0_two_shot_base.png"))

# grid 仿射格网(水平/竖直, 24px)
cx,cy=470,395; s=24.0
e1=np.array([s,0.]); e2=np.array([0.,s])
grid=base.copy()
for i in range(-24,25):
    p0=np.array([cx,cy])+i*e1-32*e2; p1=np.array([cx,cy])+i*e1+32*e2
    cv2.line(grid,tuple(p0.astype(int)),tuple(p1.astype(int)),(0,0,255),1)
for j in range(-24,25):
    p0=np.array([cx,cy])+j*e2-32*e1; p1=np.array([cx,cy])+j*e2+32*e1
    cv2.line(grid,tuple(p0.astype(int)),tuple(p1.astype(int)),(0,0,255),1)
cv2.imencode(".png",grid)[1].tofile(os.path.join(ROOT,"out","overlay","v6_l0_grid_aligned.png"))

# marks 候选标注
rec=json.load(open(os.path.join(OUT,"recog_cross.json"),encoding="utf-8"))
marks=base.copy()
off={"大本营":(16,-14),"鹰炮":(16,16),"防空塔":(16,-14),"金仓":(16,16),"法师塔":(16,-14)}
for name,d in rec.items():
    for mv,px,py in d["peaks"]:
        cxm,cym=px+35,py+40
        cv2.circle(marks,(cxm,cym),12,(120,120,120),2)
        dx,dy=off[name]
        cv2.putText(marks,f"{name}?{mv:.2f}",(cxm+dx,cym+dy),cv2.FONT_HERSHEY_SIMPLEX,0.4,(120,120,120),1)
cv2.imencode(".png",marks)[1].tofile(os.path.join(ROOT,"out","overlay","v6_l0_marks.png"))
print("final 3 images saved")
