# -*- coding: utf-8 -*-
# 子像素补偿：按相位ddy对B做亚像素平移后复测缝残差；输出最终canvas
import os, cv2, numpy as np, json
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT=os.path.join(ROOT,"out","overlay","l0new")
A=cv2.imdecode(np.fromfile(os.path.join(OUT,"A.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
B0=cv2.imdecode(np.fromfile(os.path.join(OUT,"B.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
H,W=A.shape[:2]
dy=222.6
# 先粗测
def phase(B):
    yB=int(round(dy)); ov=min(H,yB+H)-yB
    gA=cv2.cvtColor(A,cv2.COLOR_BGR2GRAY).astype(np.float64)
    gB=cv2.cvtColor(B,cv2.COLOR_BGR2GRAY).astype(np.float64)
    bandA=gA[H-ov:,:]; bandB=gB[:ov,:]
    win=cv2.createHanningWindow((W,ov),cv2.CV_64F)
    (dx,ddy),resp=cv2.phaseCorrelate(bandA,bandB,win)
    return dx,ddy,resp,ov
dx,ddy,resp,ov=phase(B0)
print("补偿前 dx=",round(dx,3),"ddy=",round(ddy,3),"resp=",round(resp,3))
# B 上移 ddy（bandB 相对 bandA 偏下 ddy），warp
M=np.float32([[1,0,0],[0,1,-ddy]])
B=cv2.warpAffine(B0,M,(W,H),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
dx2,ddy2,resp2,ov2=phase(B)
seam=float(np.hypot(dx2,ddy2))
print("补偿后 dx=",round(dx2,3),"ddy=",round(ddy2,3),"resp=",round(resp2,3),"缝残差=",round(seam,3))
yB=int(round(dy))
canvas=np.zeros((H+yB,W,3),np.uint8)
canvas[:H]=A; canvas[yB:yB+H]=B
# ORB 复核
det=cv2.ORB_create(1500)
gA=cv2.cvtColor(A,cv2.COLOR_BGR2GRAY); gB=cv2.cvtColor(B,cv2.COLOR_BGR2GRAY)
bandA=gA[H-ov2:,:]; bandB=gB[:ov2,:]
ka,da=det.detectAndCompute(bandA,None); kb,db=det.detectAndCompute(bandB,None)
bf=cv2.BFMatcher(cv2.NORM_HAMMING)
good=[m for m,n in bf.knnMatch(da,db,k=2) if m.distance<0.75*n.distance]
pa=np.float32([ka[m.queryIdx].pt for m in good]); pb=np.float32([kb[m.trainIdx].pt for m in good])
d=pb-pa; mx,my=np.median(d,axis=0)
inl=np.linalg.norm(d-[mx,my],axis=1)<12
print(f"ORB inl={int(inl.sum())}/{len(good)} shift=({mx:.2f},{my:.2f}) overlap={ov2}px={ov2/24:.1f}格")
cv2.imencode(".png",canvas)[1].tofile(os.path.join(ROOT,"out","overlay","v6_l0_two_shot_base.png"))
json.dump({"dy":dy,"subpx_comp":-ddy,"seam_resid":seam,"resp":resp2,"orb_inl":int(inl.sum()),"orb_good":len(good),"orb_shift":[float(mx),float(my)],"overlap_px":ov2,"overlap_tiles":round(ov2/24,2),"canvas":[W,int(canvas.shape[0])]},open(os.path.join(OUT,"stitch.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print("canvas",canvas.shape)
