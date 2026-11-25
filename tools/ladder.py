# -*- coding: utf-8 -*-
# 档位阶梯：先 pinch-in 到最远(L0, MAD=0)，再逐档 pinch-out 到最大(Ln, MAD=0)。
# 每帧用 v6_tile_px.measure_tile_px 实测。纯输入+截图，不读内存。
import subprocess, time, os, sys, json
import numpy as np, cv2
sys.path.insert(0, r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\tools")
from v6_tile_px import measure_tile_px

ADB = r"E:\leidian\LDPlayer9\adb.exe"
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(ROOT, "out", "overlay", "ladder")
os.makedirs(OUT, exist_ok=True)

def sh(args, binary=False):
    cp = subprocess.run([ADB]+args, capture_output=True, timeout=30)
    return cp.stdout if binary else cp.stdout.decode("utf-8","ignore")

def frame():
    raw = sh(["exec-out","screencap","-p"], binary=True)
    return cv2.imdecode(np.frombuffer(raw,np.uint8), cv2.IMREAD_COLOR)

def save(img, name):
    cv2.imencode(".png", img)[1].tofile(os.path.join(OUT, name))

def mad(a,b):
    ga=cv2.cvtColor(a,cv2.COLOR_BGR2GRAY).astype(np.float32)
    gb=cv2.cvtColor(b,cv2.COLOR_BGR2GRAY).astype(np.float32)
    return float(np.mean(np.abs(ga-gb)))

# 推送脚本
sh(["push", os.path.join(ROOT,"tools","pinch_in.sh"), "/data/local/tmp/pinchin.sh"])
sh(["push", os.path.join(ROOT,"tools","pinch_zoom.sh"), "/data/local/tmp/pinch.sh"])

rows=[]
# ---- Phase 1: pinch-in 到最远 ----
prev=frame(); save(prev,"start.png"); plateau=0; batch=0
while batch<25:
    batch+=1
    sh(["shell","sh","/data/local/tmp/pinchin.sh","14","10"])
    time.sleep(1.6)
    cur=frame(); m=mad(prev,cur)
    print(f"[IN] b{batch:02d} MAD={m:.2f}")
    if m<1.2:
        plateau+=1
        if plateau>=2: break
    else:
        plateau=0
    prev=cur
save(cur,"zoom_L0.png")
r0=measure_tile_px(cur)
rows.append(("L0", r0, m, True))
print("L0", r0)

# ---- Phase 2: pinch-out 逐档 ----
prev=cur; plateau=0; n=0
while n<25:
    n+=1
    sh(["shell","sh","/data/local/tmp/pinch.sh","14","10"])
    time.sleep(1.6)
    cur=frame(); m=mad(prev,cur)
    r=measure_tile_px(cur)
    save(cur,f"zoom_L{n}.png")
    rows.append((f"L{n}", r, m, False))
    print(f"[OUT] L{n} MAD={m:.2f} tile={r['estimate']} {r['criteria']}")
    if m<1.2:
        plateau+=1
        if plateau>=2:
            rows[-1]=(f"L{n}", r, m, True)
            break
    else:
        plateau=0
    prev=cur

# 落盘汇总
with open(os.path.join(OUT,"ladder_report.json"),"w",encoding="utf-8") as f:
    json.dump([{"level":k,"mad":round(m,2),"top":t,**{kk:vv for kk,vv in r.items()}} for k,r,m,t in rows], f, ensure_ascii=False, indent=2)
print("DONE", len(rows))
