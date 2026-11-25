# -*- coding: utf-8 -*-
# dy网格精修：在[220..226]搜dy使重叠带MAD最小+相位resp最高；输出最佳放置与缝残差
import os, cv2, numpy as np, json
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT=os.path.join(ROOT,"out","overlay","l0new")
A=cv2.imdecode(np.fromfile(os.path.join(OUT,"A.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
B=cv2.imdecode(np.fromfile(os.path.join(OUT,"B.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
H,W=A.shape[:2]
gA=cv2.cvtColor(A,cv2.COLOR_BGR2GRAY).astype(np.float64)
gB=cv2.cvtColor(B,cv2.COLOR_BGR2GRAY).astype(np.float64)
best=None
for dy10 in range(2200,2261):
    dy=dy10/10.0; yB=int(round(dy)); ov=min(H,yB+H)-yB
    bandA=gA[H-ov:,:]; bandB=gB[:ov,:]
    win=cv2.createHanningWindow((W,ov),cv2.CV_64F)
    (dx,ddy),resp=cv2.phaseCorrelate(bandA,bandB,win)
    mad=float(np.mean(np.abs(bandA-bandB)))
    score=mad
    if best is None or score<best[0]:
        best=(mad,dy,dx,ddy,resp,ov)
    print(f"dy={dy:.1f} mad={mad:.2f} resp={resp:.3f} dx={dx:.3f} ddy={ddy:.3f}")
mad,dy,dx,ddy,resp,ov=best
print("BEST dy=",dy,"mad=",round(mad,2),"resp=",round(resp,3),"phase dx=",round(dx,3),"ddy=",round(ddy,3),"seam=",round(float(np.hypot(dx,ddy)),3))
yB=int(round(dy))
canvas=np.zeros((H+yB,W,3),np.uint8)
canvas[:H]=A; canvas[yB:yB+H]=B
cv2.imencode(".png",canvas)[1].tofile(os.path.join(ROOT,"out","overlay","v6_l0_two_shot_base.png"))
json.dump({"dy":dy,"dx":dx,"ddy":ddy,"seam_resid":float(np.hypot(dx,ddy)),"resp":resp,"overlap_px":ov,"overlap_tiles":round(ov/24,2),"canvas":[W,int(canvas.shape[0])]},open(os.path.join(OUT,"stitch.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print("canvas",canvas.shape)
