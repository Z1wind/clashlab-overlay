# -*- coding: utf-8 -*-
# v15_row.py — 反馈闭环水平行采集：小拖+相位测量，累计达target拍一块。新文件。
# 用法: python v15_row.py <outprefix> <nblocks> <dir(-1东/1西)> [target]
import subprocess, cv2, numpy as np, os, sys, time
ADB=["E:\\leidian\\LDPlayer9\\adb.exe","-s","emulator-5554"]
R=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\_recon"
X0,X1,Y0,Y1=170,1110,275,605
def shot():
    out=subprocess.run(ADB+["exec-out","screencap","-p"],capture_output=True).stdout
    arr=np.frombuffer(out,np.uint8)
    return cv2.imdecode(arr,1)
def phase(a,b):
    ga=cv2.cvtColor(a[Y0:Y1,X0:X1],cv2.COLOR_BGR2GRAY).astype(np.float64)
    gb=cv2.cvtColor(b[Y0:Y1,X0:X1],cv2.COLOR_BGR2GRAY).astype(np.float64)
    h,w=ga.shape;win=cv2.createHanningWindow((w,h),cv2.CV_64F)
    (dx,dy),resp=cv2.phaseCorrelate(ga,gb,win)
    return dx,dy,resp
def drag(dx_px,dy_px):
    # 从(640,360)拖到(640+dx,360+dy)；相机反向
    subprocess.run(ADB+["shell","sh","/data/local/tmp/drag.sh","640","360",
                        str(int(640+dx_px)),str(int(360+dy_px)),"10"],check=True)
    time.sleep(1.0)
def median_pair():
    a=shot();time.sleep(0.35);b=shot()
    return np.median(np.stack([a,b],0),0).astype(np.uint8)

prefix=sys.argv[1];n=int(sys.argv[2]);d=int(sys.argv[3]);target=float(sys.argv[4]) if len(sys.argv)>4 else 190.0
os.makedirs(os.path.join(R,"feed"),exist_ok=True)
anchor=shot()
saved=0;cum=0.0;block=0
# block0 = anchor位置
med=median_pair()
cv2.imencode(".png",med)[1].tofile(os.path.join(R,"feed",f"{prefix}_{block:02d}.png"))
print("block",block,"saved")
while saved<n-1:
    drag(-100*d,0)  # 东扫finger左; d=-1东
    fr=shot()
    dx,dy,resp=phase(anchor,fr)
    cum+=abs(dx)
    print(f"  cum {cum:.1f} dx {dx:.1f} resp {resp:.3f}")
    if cum>=target:
        med=median_pair()
        block+=1;saved+=1
        cv2.imencode(".png",med)[1].tofile(os.path.join(R,"feed",f"{prefix}_{block:02d}.png"))
        anchor=fr;cum=0.0
        print("block",block,"saved")
print("DONE",saved+1)
