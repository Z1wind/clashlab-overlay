# -*- coding: utf-8 -*-
# L0→L1：pinch-out 分批，每帧 measure_tile_px，到 ~59px 停；与 zoom_L1 参考 ORB 复核
import subprocess, time, os, sys, cv2, numpy as np
sys.path.insert(0,r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\tools")
from v6_tile_px import measure_tile_px
ADB=r"E:\leidian\LDPlayer9\adb.exe"
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
def sh(a,binary=False):
    cp=subprocess.run([ADB]+a,capture_output=True,timeout=30)
    return cp.stdout if binary else cp.stdout.decode("utf-8","ignore")
def frame():
    raw=sh(["exec-out","screencap","-p"],binary=True)
    return cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_COLOR)
ref=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","ladder","zoom_L1.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
det=cv2.ORB_create(1500)
def inl(a,b):
    ka,da=det.detectAndCompute(cv2.cvtColor(a,cv2.COLOR_BGR2GRAY),None)
    kb,db=det.detectAndCompute(cv2.cvtColor(b,cv2.COLOR_BGR2GRAY),None)
    if da is None or db is None: return 0
    bf=cv2.BFMatcher(cv2.NORM_HAMMING)
    good=[m for m,n in bf.knnMatch(da,db,k=2) if m.distance<0.75*n.distance]
    return len(good)
for rnd in range(10):
    sh(["shell","sh","/data/local/tmp/pinch.sh","14","10"]); time.sleep(1.6)
    cur=frame()
    r=measure_tile_px(cur)
    n=inl(cur,ref)
    print(f"rnd{rnd} tile={r['estimate']} n_valid={r['n_valid']} orb_vs_L1={n}")
    cv2.imencode(".png",cur)[1].tofile(os.path.join(ROOT,"out","overlay","goto_L1.png"))
    if r['estimate'] and 50<r['estimate']<68 and n>150:
        print("REACHED_L1"); break
