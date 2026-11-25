# -*- coding: utf-8 -*-
# L0 两屏：N到顶→抓A；S步移~400→抓B；ORB实测；v6_stitch拼；报缝/ORB/覆盖
import subprocess, time, os, sys, cv2, numpy as np
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
def crop(im): return im[CROP[1]:CROP[3],CROP[0]:CROP[2]]
orb=cv2.ORB_create(1500)
def orb_shift(a,b):
    ka,da=orb.detectAndCompute(cv2.cvtColor(a,cv2.COLOR_BGR2GRAY),None)
    kb,db=orb.detectAndCompute(cv2.cvtColor(b,cv2.COLOR_BGR2GRAY),None)
    bf=cv2.BFMatcher(cv2.NORM_HAMMING)
    good=[m for m,n in bf.knnMatch(da,db,k=2) if m.distance<0.75*n.distance]
    if len(good)<10: return None,0
    pa=np.float32([ka[m.queryIdx].pt for m in good]); pb=np.float32([kb[m.trainIdx].pt for m in good])
    d=pb-pa; mx,my=np.median(d,axis=0)
    inl=np.linalg.norm(d-[mx,my],axis=1)<12
    return (float(mx),float(my)),int(inl.sum())

# N 到顶
prev=crop(frame()); locked=0
for _ in range(6):
    sh(["shell","sh","/data/local/tmp/drag.sh","640","40","640","290","20"]); time.sleep(1.3)
    cur=crop(frame()); s,n=orb_shift(prev,cur)
    print("N",s,"inl=",n)
    if s and abs(s[1])<10: locked+=1
    else: locked=0
    prev=cur
    if locked>=2: break
A=prev; cv2.imencode(".png",A)[1].tofile(os.path.join(ROOT,"out","overlay","l0_A.png"))

# S 步移累计~400px
prev=A; total=0.0; B=None
for att in range(6):
    sh(["shell","sh","/data/local/tmp/drag.sh","640","420","640","200","20"]); time.sleep(1.3)
    cur=crop(frame()); s,n=orb_shift(prev,cur)
    print("S",s,"inl=",n)
    if s: total+=s[1]; prev=cur
    B=cur
    if total<-360: break
cv2.imencode(".png",B)[1].tofile(os.path.join(ROOT,"out","overlay","l0_B.png"))
print("total dy=",round(total,1))
overlap=max(0.05,min(0.8,(550+total)/550))
canvas,rep=stitch([A,B],offsets=[(0,0),(0,total)],overlap=overlap,grid=(2,1),
                  report_path=os.path.join(ROOT,"out","overlay","l0_pair_report.json"))
cv2.imencode(".png",canvas)[1].tofile(os.path.join(ROOT,"out","overlay","v6_L0_pair_stitched.png"))
for t in rep["tiles"]:
    print(t["index"],"seam=",t["seam_err_px"],"orb_med=",t["orb_med_px"],"orb_inl=",t["orb_inliers"],"pass=",t["pass"])
print("overlap=",round(overlap,3),"canvas",canvas.shape)
