# -*- coding: utf-8 -*-
# v15_wallperiod.py — 直墙带 x 方向边缘投影自相关，求墙柱/墙段周期(px)。
# 用法: python v15_wallperiod.py <frame> <x1,y1,x2,y2> [minlag]
import sys, os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EN = os.path.join(ROOT, "out", "overlay", "enemy")
frame=sys.argv[1]; box=[int(v) for v in sys.argv[2].split(",")]; minlag=int(sys.argv[3]) if len(sys.argv)>3 else 20
im=cv2.imdecode(np.fromfile(os.path.join(EN,frame),dtype=np.uint8),cv2.IMREAD_COLOR)
x1,y1,x2,y2=box
crop=im[y1:y2,x1:x2]
g=cv2.cvtColor(crop,cv2.COLOR_BGR2GRAY)
gx=cv2.Sobel(g,cv2.CV_64F,1,0,ksize=3)
col=np.abs(gx).mean(axis=0)
col=col-col.mean()
ac=np.correlate(col,col,'full')[len(col)-1:]
ac=ac/ac[0]
# 找首个主峰(跳过0)
seg=ac[minlag:]
pk=[i for i in range(2,len(seg)-2) if seg[i]==max(seg[i-2:i+3]) and seg[i]>0.05]
if pk:
    lag=pk[0]+minlag
    print(f"wall period x = {lag} px  (2a={lag}, a={lag/2:.1f}, |east|={lag/2*1.155:.1f})")
else:
    top=np.argsort(seg)[-5:]+minlag
    print("no peak; top lags:",top.tolist(),[round(float(ac[t]),3) for t in top])
vis=crop.copy()
cv2.imencode(".png",vis)[1].tofile(os.path.join(EN,"wall_debug.png"))
