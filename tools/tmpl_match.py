# -*- coding: utf-8 -*-
# tmpl_match.py — 模板全局匹配找重复实例: tmpl_x1 y1 x2 y2
import cv2, numpy as np, os, sys
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
im=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_stitched_base.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
x1,y1,x2,y2=map(int,sys.argv[1:5])
tpl=g[y1:y2,x1:x2]
res=cv2.matchTemplate(g,tpl,cv2.TM_CCOEFF_NORMED)
# 非极大抑制找峰值
r=res.copy(); peaks=[]
for _ in range(8):
    _,mx,_,ml=cv2.minMaxLoc(r)
    if mx<0.6: break
    peaks.append((ml[0],ml[1],round(mx,3)))
    cv2.rectangle(r,(ml[0]-80,ml[1]-80),(ml[0]+80,ml[1]+80),-1,-1)
for p in peaks: print("match at",p)
vis=im.copy()
for x,y,s in peaks:
    cv2.rectangle(vis,(x,y),(x+(x2-x1),y+(y2-y1)),(0,0,255),3)
    cv2.putText(vis,f"{s}",(x,y-8),cv2.FONT_HERSHEY_SIMPLEX,0.8,(0,0,255),2)
cv2.imencode(".png",vis)[1].tofile(os.path.join(ROOT,"out","overlay","tmpl_hits.png"))
