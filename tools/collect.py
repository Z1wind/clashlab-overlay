# -*- coding: utf-8 -*-
# collect.py — Step2 自动步进采集：方向步进→抓帧→相位相关实测位移→裁UI存块→累积偏移JSON
# 用法:
#   python collect.py init <name>                 # 以当前帧为块0，偏移(0,0)
#   python collect.py step <dir> <len> [n]       # dir=up/down/left/right; 每步swipe len px; 实测位移; 边缘(|<10px|)自动停
# 块存 out/overlay/blocks/bNN.png；日志 out/overlay/blocks/collect_log.json
import subprocess, sys, os, json, time, cv2, numpy as np
ADB=r"E:\leidian\LDPlayer9\adb.exe"
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
LAD=os.path.join(ROOT,"out","overlay","ladder")
BLK=os.path.join(ROOT,"out","overlay","blocks")
os.makedirs(BLK,exist_ok=True)
LOG=os.path.join(BLK,"collect_log.json")
CROP=(155,80,1105,630)
SAFE_Y=(180,420)

def grab():
    raw=subprocess.run([ADB,"exec-out","screencap","-p"],capture_output=True,timeout=30).stdout
    return cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_COLOR)

def _crop_if_full(im):
    x1,y1,x2,y2=CROP
    if im.shape[0]==720 and im.shape[1]==1280:
        return im[y1:y2,x1:x2]
    return im

def corr(ia,ib):
    # 两图均可全帧或已裁；统一裁到同尺寸
    ia=_crop_if_full(ia); ib=_crop_if_full(ib)
    ga=cv2.cvtColor(ia,cv2.COLOR_BGR2GRAY).astype(np.float64)
    gb=cv2.cvtColor(ib,cv2.COLOR_BGR2GRAY).astype(np.float64)
    win=cv2.createHanningWindow((ga.shape[1],ga.shape[0]),cv2.CV_64F)
    (dx,dy),resp=cv2.phaseCorrelate(ga,gb,win)
    return float(dx),float(dy),float(resp)

def swipe(x1,y1,x2,y2,ms=280):
    subprocess.run([ADB,"shell","input","swipe",str(x1),str(y1),str(x2),str(y2),str(ms)],timeout=30)

def load_log():
    if os.path.exists(LOG):
        return json.load(open(LOG,encoding="utf-8"))
    return {"tiles":[],"cx":0.0,"cy":0.0,"last":None}

def save_log(d):
    json.dump(d,open(LOG,"w",encoding="utf-8"),ensure_ascii=False,indent=2)

def crop_save(img,name):
    x1,y1,x2,y2=CROP
    cv2.imencode(".png",img[y1:y2,x1:x2])[1].tofile(os.path.join(BLK,name))

if __name__=="__main__":
    cmd=sys.argv[1]
    log=load_log()
    if cmd=="init":
        img=grab()
        n=len(log["tiles"])
        name=f"b{n:02d}.png"
        crop_save(img,name)
        log["tiles"].append({"file":name,"dx":0.0,"dy":0.0,"cx":0.0,"cy":0.0,"resp":1.0})
        log["last"]=name; log["cx"]=0.0; log["cy"]=0.0
        save_log(log)
        print("init",name)
    elif cmd=="step":
        d=sys.argv[2]; L=int(sys.argv[3]); n=int(sys.argv[4]) if len(sys.argv)>4 else 1
        prev=cv2.imdecode(np.fromfile(os.path.join(BLK,log["last"]),dtype=np.uint8),cv2.IMREAD_COLOR)
        for k in range(n):
            # 安全带 y=220 空地，x 380-820，避开按钮/导轨
            if d=="up":   swipe(640,360,640,360-L)
            elif d=="down": swipe(640,180,640,180+L)
            elif d=="left": swipe(860,220,860-L,220)
            elif d=="right":swipe(420,220,420+L,220)
            time.sleep(0.9)
            img=grab()
            dx,dy,resp=corr(prev,img)
            print(f"step{k}: measured dx={dx:.1f} dy={dy:.1f} resp={resp:.2f}")
            if (abs(dx)<10 and abs(dy)<10):
                print("EDGE stop"); break
            print(f"resp={resp:.2f}")
            log["cx"]+=dx; log["cy"]+=dy
            name=f"b{len(log['tiles']):02d}.png"
            crop_save(img,name)
            log["tiles"].append({"file":name,"dx":round(dx,2),"dy":round(dy,2),
                                 "cx":round(log["cx"],2),"cy":round(log["cy"],2),"resp":round(resp,3)})
            log["last"]=name
            prev=img
            save_log(log)
        save_log(log)
