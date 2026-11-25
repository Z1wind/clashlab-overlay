# -*- coding: utf-8 -*-
# collect2.py — sendevent drag 版采集：init / drag<dir> <len> [n] / 手动列块
# dir=E(看东, finger左) / W(finger右) / S(finger上) / N(finger下)
# 每步 drag.sh → grab → 与上一块相位相关 → 累积偏移存 blocks/
import subprocess, sys, os, json, time, cv2, numpy as np
ADB=r"E:\leidian\LDPlayer9\adb.exe"
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
LAD=os.path.join(ROOT,"out","overlay","ladder")
BLK=os.path.join(ROOT,"out","overlay","blocks")
os.makedirs(BLK,exist_ok=True)
LOG=os.path.join(BLK,"collect_log.json")
CROP=(155,80,1105,630)

def grab():
    raw=subprocess.run([ADB,"exec-out","screencap","-p"],capture_output=True,timeout=30).stdout
    return cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_COLOR)

def _c(im):
    x1,y1,x2,y2=CROP
    return im[y1:y2,x1:x2] if im.shape[:2]==(720,1280) else im

def corr(ia,ib):
    ga=cv2.cvtColor(_c(ia),cv2.COLOR_BGR2GRAY).astype(np.float64)
    gb=cv2.cvtColor(_c(ib),cv2.COLOR_BGR2GRAY).astype(np.float64)
    win=cv2.createHanningWindow((ga.shape[1],ga.shape[0]),cv2.CV_64F)
    (dx,dy),resp=cv2.phaseCorrelate(ga,gb,win)
    return float(dx),float(dy),float(resp)

def drag(dx,dy,L):
    # 水平从(640,220)；垂直从(640,420)，均在安全带内
    if dy==0:
        x0,y0=(900,220) if dx<0 else (380,220)
    elif dy<0:
        x0,y0=640,420
    else:
        x0,y0=640,40
    x1=int(x0+dx*L); y1=int(y0+dy*L)
    y1=max(20,min(460,y1)); x1=max(360,min(920,x1))
    subprocess.run([ADB,"shell","sh","/data/local/tmp/drag.sh",str(x0),str(y0),str(x1),str(y1),"14"],timeout=30)

def load_log():
    if os.path.exists(LOG): return json.load(open(LOG,encoding="utf-8"))
    return {"tiles":[],"cx":0.0,"cy":0.0,"last":None}
def save_log(d): json.dump(d,open(LOG,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
def crop_save(img,name):
    x1,y1,x2,y2=CROP
    cv2.imencode(".png",img[y1:y2,x1:x2])[1].tofile(os.path.join(BLK,name))

DIR={"E":(-1,0),"W":(1,0),"S":(0,-1),"N":(0,1)}

if __name__=="__main__":
    cmd=sys.argv[1]; log=load_log()
    if cmd=="init":
        img=grab(); name=f"b{len(log['tiles']):02d}.png"; crop_save(img,name)
        log["tiles"].append({"file":name,"dx":0,"dy":0,"cx":0,"cy":0,"resp":1})
        log["last"]=name; log["cx"]=0; log["cy"]=0; save_log(log); print("init",name)
    elif cmd=="drag":
        d=sys.argv[2]; L=int(sys.argv[3]); n=int(sys.argv[4]) if len(sys.argv)>4 else 1
        prev=cv2.imdecode(np.fromfile(os.path.join(BLK,log["last"]),dtype=np.uint8),cv2.IMREAD_COLOR)
        vx,vy=DIR[d]
        for k in range(n):
            drag(vx,vy,L); time.sleep(1.0)
            img=grab(); dx,dy,resp=corr(prev,img)
            print(f"step{k}: dx={dx:.1f} dy={dy:.1f} resp={resp:.2f}")
            if abs(dx)<12 and abs(dy)<12:
                print("EDGE stop"); break
            log["cx"]+=dx; log["cy"]+=dy
            name=f"b{len(log['tiles']):02d}.png"; crop_save(img,name)
            log["tiles"].append({"file":name,"dx":round(dx,1),"dy":round(dy,1),
                                 "cx":round(log["cx"],1),"cy":round(log["cy"],1),"resp":round(resp,2)})
            log["last"]=name; prev=img; save_log(log)
        save_log(log)
