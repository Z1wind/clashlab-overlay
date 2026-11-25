# -*- coding: utf-8 -*-
# L0 上下两屏：抓A → S拖(重试到动) → 抓B；ORB测位移；v6_stitch拼；报缝残差/ORB
import subprocess, time, os, sys, json, cv2, numpy as np
sys.path.insert(0,r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\tools")
from v6_stitch import stitch
ADB=r"E:\leidian\LDPlayer9\adb.exe"
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
CROP=(155,80,1105,630)
def sh(a,binary=False):
    cp=subprocess.run([ADB]+a,capture_output=True,timeout=30)
    return cp.stdout if binary else cp.stdout.decode("utf-8","ignore")
def frame():
    raw=sh(["exec-out","screencap","-p"],binary=True)
    return cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_COLOR)
def crop(im):
    x1,y1,x2,y2=CROP; return im[y1:y2,x1:x2]
orb=cv2.ORB_create(1500)
def orb_shift(a,b):
    ka,da=orb.detectAndCompute(cv2.cvtColor(a,cv2.COLOR_BGR2GRAY),None)
    kb,db=orb.detectAndCompute(cv2.cvtColor(b,cv2.COLOR_BGR2GRAY),None)
    bf=cv2.BFMatcher(cv2.NORM_HAMMING)
    good=[m for m,n in bf.knnMatch(da,db,k=2) if m.distance<0.75*n.distance]
    if len(good)<10: return None,0,len(good)
    pa=np.float32([ka[m.queryIdx].pt for m in good]); pb=np.float32([kb[m.trainIdx].pt for m in good])
    d=pb-pa; mx,my=np.median(d,axis=0)
    inl=np.linalg.norm(d-[mx,my],axis=1)<12
    return (float(mx),float(my)),int(inl.sum()),len(good)

A=frame(); Ac=crop(A); prev=Ac; total=0.0; nin=0
for att in range(4):
    sh(["shell","sh","/data/local/tmp/drag.sh","640","420","640","20","24"]); time.sleep(1.6)
    B=frame(); Bc=crop(B)
    shift,nin,ng=orb_shift(prev,Bc)
    print(f"att{att} shift={shift} inl={nin} good={ng}")
    if shift:
        total+=shift[1]; prev=Bc
    if abs(total)>200: break
if abs(total)<200:
    print("FAIL no pan"); sys.exit(1)
Ac=A; Bc=prev; dy=total
overlap=max(0.05,min(0.8,(550+dy)/550))
canvas,rep=stitch([Ac,Bc],offsets=[(0,0),(0,dy)],overlap=overlap,grid=(2,1),
                  report_path=os.path.join(ROOT,"out","overlay","l0_pair_report.json"))
cv2.imencode(".png",canvas)[1].tofile(os.path.join(ROOT,"out","overlay","v6_L0_pair_stitched.png"))
for t in rep["tiles"]:
    print(t["index"],"seam=",t["seam_err_px"],"orb_med=",t["orb_med_px"],"orb_inl=",t["orb_inliers"],"pass=",t["pass"])
print("dy=",round(dy,1),"overlap=",round(overlap,3),"canvas",canvas.shape)
