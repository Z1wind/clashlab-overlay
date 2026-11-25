# -*- coding: utf-8 -*-
# L0 导航：W 步移向村庄，ORB 对 zoom_L0 参考帧；到中心后停
import subprocess, time, os, cv2, numpy as np
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
ref=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","ladder","zoom_L0.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
refc=crop(ref)
orb=cv2.ORB_create(1500)
def inl_vs_ref(im):
    ka,da=orb.detectAndCompute(cv2.cvtColor(im,cv2.COLOR_BGR2GRAY),None)
    kb,db=orb.detectAndCompute(cv2.cvtColor(refc,cv2.COLOR_BGR2GRAY),None)
    if da is None or db is None: return 0,None
    bf=cv2.BFMatcher(cv2.NORM_HAMMING)
    good=[m for m,n in bf.knnMatch(da,db,k=2) if m.distance<0.75*n.distance]
    if len(good)<10: return len(good),None
    pa=np.float32([ka[m.queryIdx].pt for m in good]); pb=np.float32([kb[m.trainIdx].pt for m in good])
    d=pb-pa; mx,my=np.median(d,axis=0)
    inn=np.linalg.norm(d-[mx,my],axis=1)<15
    return int(inn.sum()),(float(mx),float(my))
for step in range(8):
    f=crop(frame())
    n,sh_=inl_vs_ref(f)
    print(f"step{step} inl={n} shift={sh_}")
    if n>=350:
        print("CENTERED"); break
    sh(["shell","sh","/data/local/tmp/drag.sh","380","220","620","220","20"]); time.sleep(1.4)
cv2.imencode(".png",f)[1].tofile(os.path.join(ROOT,"out","overlay","l0_nav.png"))
