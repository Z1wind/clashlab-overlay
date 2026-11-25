# -*- coding: utf-8 -*-
# 三帧竖链拼接：ORB粗偏移 -> 相位精修 -> 子像素补偿；报每缝残差/ORB内点；存canvas
import cv2, numpy as np, os, json
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT=os.path.join(ROOT,"out","overlay","l0three")
frames=[cv2.imdecode(np.fromfile(os.path.join(OUT,f"f{i}.png"),dtype=np.uint8),cv2.IMREAD_COLOR) for i in range(3)]
meta=json.load(open(os.path.join(OUT,"chain.json"),encoding="utf-8"))
H,W=frames[0].shape[:2]
ypos=[m["y"] for m in meta]
# 逐关节相位精修
def phase(bandA,bandB):
    win=cv2.createHanningWindow((bandA.shape[1],bandA.shape[0]),cv2.CV_64F)
    (dx,ddy),resp=cv2.phaseCorrelate(bandA.astype(np.float64),bandB.astype(np.float64),win)
    return dx,ddy,resp
placed=[frames[0]]
offs=[0.0]
seams=[]
for k in range(1,3):
    yb=ypos[k]
    prev_y=offs[-1]
    ov=int(round(prev_y+H))-int(round(yb))
    gA=cv2.cvtColor(frames[k-1],cv2.COLOR_BGR2GRAY)
    gB=cv2.cvtColor(frames[k],cv2.COLOR_BGR2GRAY)
    bandA=gA[H-ov:,:]; bandB=gB[:ov,:]
    dx,ddy,resp=phase(bandA,bandB)
    yb+=ddy
    # 子像素补偿B
    M=np.float32([[1,0,0],[0,1,-ddy]])
    Bc=cv2.warpAffine(frames[k],M,(W,H),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
    # 补偿后复测
    gB2=cv2.cvtColor(Bc,cv2.COLOR_BGR2GRAY)
    bandB2=gB2[:ov,:]
    dx2,ddy2,resp2=phase(bandA,bandB2)
    seam=float(np.hypot(dx2,ddy2))
    # ORB复核
    det=cv2.ORB_create(1500)
    ka,da=det.detectAndCompute(bandA,None); kb,db=det.detectAndCompute(bandB2,None)
    bf=cv2.BFMatcher(cv2.NORM_HAMMING)
    good=[m for m,n in bf.knnMatch(da,db,k=2) if m.distance<0.75*n.distance]
    if len(good)>=10:
        pa=np.float32([ka[m.queryIdx].pt for m in good]); pb=np.float32([kb[m.trainIdx].pt for m in good])
        d=pb-pa; mx,my=np.median(d,axis=0)
        inl=np.linalg.norm(d-[mx,my],axis=1)<12
        ninl=int(inl.sum())
    else:
        ninl=0; mx=my=0.0
    seams.append({"joint":k,"dy":round(yb,2),"seam":round(seam,3),"resp":round(resp2,3),"orb_inl":ninl,"orb_good":len(good),"orb_shift":[round(float(mx),2),round(float(my),2)],"overlap_px":ov,"overlap_tiles":round(ov/24,2)})
    offs.append(yb); placed.append(Bc)
    print(f"joint{k} dy={yb:.2f} seam={seam:.3f} resp={resp2:.3f} ORB={ninl}/{len(good)} ov={ov}px={ov/24:.1f}格")
# 放置
maxy=int(round(offs[-1]+H))
canvas=np.zeros((maxy,W,3),np.uint8)
for fr,y in zip(placed,offs):
    y0=int(round(y)); canvas[y0:y0+H]=fr
cv2.imencode(".png",canvas)[1].tofile(os.path.join(ROOT,"out","overlay","v6_l0_three_shot_base.png"))
json.dump({"offs":offs,"seams":seams,"canvas":[W,maxy],"canvas_tiles":[round(W/24,1),round(maxy/24,1)]},open(os.path.join(OUT,"stitch3.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print("canvas",canvas.shape,"格",round(W/24,1),"x",round(maxy/24,1))
