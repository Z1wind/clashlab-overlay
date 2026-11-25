# -*- coding: utf-8 -*-
# 新A/B拼接：ORB粗dy -> 相位相关精修 -> 放置；报缝残差/ORB内点；存canvas
import os, cv2, numpy as np, json
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT=os.path.join(ROOT,"out","overlay","l0new")
A=cv2.imdecode(np.fromfile(os.path.join(OUT,"A.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
B=cv2.imdecode(np.fromfile(os.path.join(OUT,"B.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
rep=json.load(open(os.path.join(OUT,"capture.json"),encoding="utf-8"))
dy0=abs(rep["dy_orb"])
H,W=A.shape[:2]
# 相位相关精修重叠带（先按粗dy取带）
yB=int(round(dy0)); ov=min(H,yB+H)-yB
gA=cv2.cvtColor(A,cv2.COLOR_BGR2GRAY).astype(np.float64)
gB=cv2.cvtColor(B,cv2.COLOR_BGR2GRAY).astype(np.float64)
bandA=gA[H-ov:,:]; bandB=gB[:ov,:]
win=cv2.createHanningWindow((W,ov),cv2.CV_64F)
(dx,ddy),resp=cv2.phaseCorrelate(bandA,bandB,win)
dy=yB+ddy
print(f"粗dy={dy0} phase dx={dx:.3f} ddy={ddy:.3f} resp={resp:.3f} -> dy={dy:.3f}")
yB=int(round(dy))
canvas=np.zeros((H+yB,W,3),np.uint8)
canvas[:H]=A
canvas[yB:yB+H]=B
# 重叠带复核（精修后）
ov2=min(H,yB+H)-yB
bandA2=gA[H-ov2:,:]; bandB2=gB[:ov2,:]
(dx2,ddy2),resp2=cv2.phaseCorrelate(bandA2,bandB2,win)
seam=float(np.hypot(dx2,ddy2))
det=cv2.ORB_create(1500)
ka,da=det.detectAndCompute(bandA2.astype(np.uint8),None)
kb,db=det.detectAndCompute(bandB2.astype(np.uint8),None)
bf=cv2.BFMatcher(cv2.NORM_HAMMING)
good=[m for m,n in bf.knnMatch(da,db,k=2) if m.distance<0.75*n.distance]
pa=np.float32([ka[m.queryIdx].pt for m in good]); pb=np.float32([kb[m.trainIdx].pt for m in good])
d=pb-pa; mx,my=np.median(d,axis=0)
inl=np.linalg.norm(d-[mx,my],axis=1)<12
print(f"缝残差={seam:.3f}px resp={resp2:.3f} ORB inl={int(inl.sum())}/{len(good)} shift=({mx:.1f},{my:.1f}) overlap={ov2}px={ov2/24:.1f}格")
cv2.imencode(".png",canvas)[1].tofile(os.path.join(ROOT,"out","overlay","v6_l0_two_shot_base.png"))
print("canvas",canvas.shape,"总高",canvas.shape[0],"px=",round(canvas.shape[0]/24,1),"格 宽",W,"px=",round(W/24,1),"格")
json.dump({"dy":dy,"dx":dx,"seam_resid":seam,"resp":resp2,"orb_inl":int(inl.sum()),"orb_good":len(good),"overlap_px":ov2,"overlap_tiles":round(ov2/24,2),"canvas":[W,canvas.shape[0]]},open(os.path.join(OUT,"stitch.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
