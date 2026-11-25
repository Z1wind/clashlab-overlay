# -*- coding: utf-8 -*-
# collect3.py — ORB 门控采集：drag→ORB测位移→inl<20 按残差补拖重试(≤3)，记录实测链
import subprocess, sys, os, json, time, cv2, numpy as np, re
ADB=r"E:\leidian\LDPlayer9\adb.exe"
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
LAD=os.path.join(ROOT,"out","overlay","ladder")
BLK=os.path.join(ROOT,"out","overlay","blocks3")
os.makedirs(BLK,exist_ok=True)
LOG=os.path.join(BLK,"collect_log.json")
CROP=(155,80,1105,630)
orb=cv2.ORB_create(1200)

def grab():
    raw=subprocess.run([ADB,"exec-out","screencap","-p"],capture_output=True,timeout=30).stdout
    return cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_COLOR)

def crop(im):
    x1,y1,x2,y2=CROP; return im[y1:y2,x1:x2]

def orb_match(a,b):
    ga=cv2.cvtColor(a,cv2.COLOR_BGR2GRAY); gb=cv2.cvtColor(b,cv2.COLOR_BGR2GRAY)
    ka,da=orb.detectAndCompute(ga,None); kb,db=orb.detectAndCompute(gb,None)
    if da is None or db is None or len(ka)<10 or len(kb)<10: return None,0
    bf=cv2.BFMatcher(cv2.NORM_HAMMING)
    knn=bf.knnMatch(da,db,k=2)
    good=[m for m,n in knn if m.distance<0.75*n.distance]
    if len(good)<8: return None,len(good)
    pa=np.float32([ka[m.queryIdx].pt for m in good])
    pb=np.float32([kb[m.trainIdx].pt for m in good])
    d=pb-pa
    mx,my=np.median(d,axis=0)
    inl=np.linalg.norm(d-[mx,my],axis=1)<10
    if inl.sum()>=6: mx,my=np.median(d[inl],axis=0)
    return (float(mx),float(my)),int(inl.sum())

def drag(dx,dy,L):
    if dy==0:
        x0,y0=(900,220) if dx<0 else (380,220)
    elif dy<0:
        x0,y0=640,420
    else:
        x0,y0=640,40
    x1=int(x0+dx*L); y1=int(y0+dy*L)
    y1=max(20,min(460,y1)); x1=max(360,min(920,x1))
    subprocess.run([ADB,"shell","sh","/data/local/tmp/drag.sh",str(x0),str(y0),str(x1),str(y1),"16"],timeout=30)

def next_name(log):
    mx=0
    for t in log["tiles"]:
        m=re.match(r"b(\d+)",t["file"])
        if m: mx=max(mx,int(m.group(1)))
    return f"b{mx+1:02d}.png"

def load_log():
    if os.path.exists(LOG): return json.load(open(LOG,encoding="utf-8"))
    return {"tiles":[],"last":None}
def save_log(d): json.dump(d,open(LOG,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
def save(im,name):
    cv2.imencode(".png",crop(im))[1].tofile(os.path.join(BLK,name))

DIR={"E":(-1,0),"W":(1,0),"S":(0,-1),"N":(0,1)}

if __name__=="__main__":
    cmd=sys.argv[1]; log=load_log()
    if cmd=="init":
        im=grab(); name=next_name(log); save(im,name)
        log["tiles"].append({"file":name,"dx":0,"dy":0,"inl":99,"ok":True})
        log["last"]=name; save_log(log); print("init",name)
    elif cmd=="step":
        d=sys.argv[2]; L=float(sys.argv[3]); n=int(sys.argv[4]) if len(sys.argv)>4 else 1
        vx,vy=DIR[d]
        for k in range(n):
            prev=cv2.imdecode(np.fromfile(os.path.join(BLK,log["last"]),dtype=np.uint8),cv2.IMREAD_COLOR)
            got=None; attempts=0
            while attempts<3:
                attempts+=1
                drag(vx,vy,L)
                time.sleep(1.0)
                im=grab()
                s,nin=orb_match(prev,crop(im))
                got=s  # 每次重测覆盖，不累积
                if nin>=20: break
                print(f"  retry{attempts} inl={nin}")
            name=next_name(log); save(im,name)
            ok=nin>=20
            log["tiles"].append({"file":name,"dx":round(got[0],1) if got else None,
                                 "dy":round(got[1],1) if got else None,
                                 "inl":nin,"ok":bool(ok),"att":attempts})
            log["last"]=name; save_log(log)
            print(f"{name} dx={got[0] if got else None:.1f} dy={got[1] if got else None:.1f} inl={nin} ok={ok} att={attempts}")
