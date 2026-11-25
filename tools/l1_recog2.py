# -*- coding: utf-8 -*-
# L1 跨帧 NCC：模板来自A帧，搜B帧（非同帧自匹配），报峰值/ratio
import cv2, numpy as np, os
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT=os.path.join(ROOT,"out","overlay","blocks_L1")
def load(f): return cv2.imdecode(np.fromfile(os.path.join(OUT,f),dtype=np.uint8),cv2.IMREAD_COLOR)
def ncc(img,tpl):
    g=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY).astype(np.float32)
    t=cv2.cvtColor(tpl,cv2.COLOR_BGR2GRAY).astype(np.float32)
    res=cv2.matchTemplate(g,t,cv2.TM_CCOEFF_NORMED)
    r=res.copy(); _,mx,_,ml=cv2.minMaxLoc(r)
    r[max(0,ml[1]-100):ml[1]+100,max(0,ml[0]-100):ml[0]+100]=-1
    _,mx2,_,_=cv2.minMaxLoc(r)
    return float(mx),float(mx2),ml
# 金仓: l1_00模板 -> 搜 l1_03/l1_04
# 法师塔: l1_00模板 -> 搜 l1_04
cases=[
 ("金仓","l1_00.png",(340,330,560,555),"l1_04.png"),
 ("法师塔","l1_00.png",(580,400,780,555),"l1_04.png"),
 ("金仓","l1_00.png",(340,330,560,555),"l1_03.png"),
]
for name,src,box,dst in cases:
    a=load(src); b=load(dst)
    x0,y0,x1,y1=box
    best=(-1,0,0,None)
    for dx in (-10,-5,0,5,10):
        for dy in (-10,-5,0,5,10):
            tt=a[max(0,y0+dy):y1+dy,max(0,x0+dx):x1+dx]
            if tt.shape[:2]!=(y1-y0,x1-x0): continue
            p,s,ml=ncc(b,tt)
            if p>best[0]: best=(p,s,ml,src)
    peak,second,ml,_=best
    ratio=peak/second if second>0 else 9.9
    v="认出" if peak>0.75 and ratio>1.5 else ("勉强" if peak>=0.6 else "认不出")
    print(f"{name} {src}->{dst}: peak={peak:.3f} second={second:.3f} ratio={ratio:.2f} @{ml} {v}")
