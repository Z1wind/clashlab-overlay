# -*- coding: utf-8 -*-
# sweep.py — Step2 采集驱动：grab / corr / swipe / crop，纯 adb+离线
# 用法:
#   python sweep.py grab <name>
#   python sweep.py corr <a> <b>          # b相对a 位移
#   python sweep.py swipe x1 y1 x2 y2 [ms]
#   python sweep.py crop <name> <out>     # 裁UI条带存 blocks/
import subprocess, sys, os, cv2, numpy as np
ADB=r"E:\leidian\LDPlayer9\adb.exe"
LAD=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\ladder"
BLK=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\blocks"
os.makedirs(BLK,exist_ok=True)
# 设备坐标 UI 条带（z1 实测）：顶资源条 y0-78；左名牌 x0-152；底任务栏 y632-720；右导轨 x1108-1280
CROP=(155,80,1105,630)

def grab(name):
    raw=subprocess.run([ADB,"exec-out","screencap","-p"],capture_output=True,timeout=30).stdout
    img=cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_COLOR)
    cv2.imencode(".png",img)[1].tofile(os.path.join(LAD,name))
    print("saved",name,img.shape)

def corr(a,b):
    ia=cv2.imdecode(np.fromfile(os.path.join(LAD,a),dtype=np.uint8),cv2.IMREAD_COLOR)
    ib=cv2.imdecode(np.fromfile(os.path.join(LAD,b),dtype=np.uint8),cv2.IMREAD_COLOR)
    ga=cv2.cvtColor(ia,cv2.COLOR_BGR2GRAY).astype(np.float64)
    gb=cv2.cvtColor(ib,cv2.COLOR_BGR2GRAY).astype(np.float64)
    x1,y1,x2,y2=CROP
    ga=ga[y1:y2,x1:x2]; gb=gb[y1:y2,x1:x2]
    win=cv2.createHanningWindow((ga.shape[1],ga.shape[0]),cv2.CV_64F)
    (dx,dy),resp=cv2.phaseCorrelate(ga,gb,win)
    print(f"dx={dx:.2f} dy={dy:.2f} resp={resp:.3f}")
    return dx,dy,resp

def swipe(x1,y1,x2,y2,ms=300):
    subprocess.run([ADB,"shell","input","swipe",str(x1),str(y1),str(x2),str(y2),str(ms)],timeout=30)

def crop(name,out):
    img=cv2.imdecode(np.fromfile(os.path.join(LAD,name),dtype=np.uint8),cv2.IMREAD_COLOR)
    x1,y1,x2,y2=CROP
    c=img[y1:y2,x1:x2]
    cv2.imencode(".png",c)[1].tofile(os.path.join(BLK,out))
    print("cropped",out,c.shape)

if __name__=="__main__":
    cmd=sys.argv[1]
    if cmd=="grab": grab(sys.argv[2])
    elif cmd=="corr": corr(sys.argv[2],sys.argv[3])
    elif cmd=="swipe":
        m=sys.argv[6] if len(sys.argv)>6 else 300
        swipe(int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4]),int(sys.argv[5]),int(m))
    elif cmd=="crop": crop(sys.argv[2],sys.argv[3])
