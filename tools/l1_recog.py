# -*- coding: utf-8 -*-
# L1 单尺度 NCC：模板抠自 L1 帧，搜 v6_L1_6blocks；报峰值/peak ratio
import cv2, numpy as np, os
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT=os.path.join(ROOT,"out","overlay","blocks_L1")
canvas=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_L1_6blocks.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
# (名, 模板来源帧, x0,y0,x1,y1, 是否在覆盖带内)
TPL={
 "金仓":("l1_00.png",(330,320,570,555),True),
 "法师塔":("l1_00.png",(560,380,800,555),True),
 "防空塔":("l1_01.png",(300,150,520,360),False),
 "鹰炮":("l1_04.png",(0,0,220,180),False),
 "大本营":("l1_04.png",(600,300,860,555),False),
}
def ncc(img,tpl):
    g=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY).astype(np.float32)
    t=cv2.cvtColor(tpl,cv2.COLOR_BGR2GRAY).astype(np.float32)
    res=cv2.matchTemplate(g,t,cv2.TM_CCOEFF_NORMED)
    r=res.copy(); _,mx,_,ml=cv2.minMaxLoc(r)
    r[max(0,ml[1]-100):ml[1]+100,max(0,ml[0]-100):ml[0]+100]=-1
    _,mx2,_,_=cv2.minMaxLoc(r)
    return float(mx),float(mx2),ml
hit=0
for name,(src,box,present) in TPL.items():
    tpl=cv2.imdecode(np.fromfile(os.path.join(OUT,src),dtype=np.uint8),cv2.IMREAD_COLOR)
    x0,y0,x1,y1=box; t=tpl[y0:y1,x0:x1]
    best=(-1,None,None,None)
    for dx in (-10,-5,0,5,10):
        for dy in (-10,-5,0,5,10):
            tt=tpl[max(0,y0+dy):y1+dy,max(0,x0+dx):x1+dx]
            if tt.shape[:2]!=t.shape[:2]: continue
            p,s,ml=ncc(canvas,tt)
            if p>best[0]: best=(p,s,ml,src)
    peak,second,ml,src=best
    ratio=peak/second if second>0 else 9.9
    verdict="认出" if peak>0.75 and ratio>1.5 else ("勉强" if peak>=0.6 else "认不出")
    if verdict=="认出" and present: hit+=1
    print(f"{name}: peak={peak:.3f} second={second:.3f} ratio={ratio:.2f} @{ml} {verdict} (覆盖带内={present})")
print("n/5 =",hit)
