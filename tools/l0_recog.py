# -*- coding: utf-8 -*-
# L0 单尺度 NCC 识别：模板抠自 zoom_L0，±10px 平移正样本；在 l0_A 与拼图上匹配
# 判据：峰值>0.75 且 peak ratio(峰/次峰)>1.5 = 认出；<0.6 认不出；中间=勉强
import cv2, numpy as np, os
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ref=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","ladder","zoom_L0.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
R=ref[80:630,155:1060]
tests={
 "l0_A":cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","l0_A.png"),dtype=np.uint8),cv2.IMREAD_COLOR),
 "pair":cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_L0_pair_stitched.png"),dtype=np.uint8),cv2.IMREAD_COLOR),
}
# (名, x0,y0,x1,y1) 模板盒（zoom_L0 裁片坐标）
TPL={
 "大本营":(560,220,645,305),
 "鹰炮":(375,275,460,360),
 "防空塔":(505,358,580,418),
 "金仓":(398,338,472,408),
 "法师塔":(505,338,580,408),
}
def ncc_peak(img,tpl):
    g=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY).astype(np.float32)
    t=cv2.cvtColor(tpl,cv2.COLOR_BGR2GRAY).astype(np.float32)
    res=cv2.matchTemplate(g,t,cv2.TM_CCOEFF_NORMED)
    # NMS：主峰，屏蔽周边90px，取次峰
    r=res.copy()
    _,mx,_,ml=cv2.minMaxLoc(r)
    r[max(0,ml[1]-90):ml[1]+90,max(0,ml[0]-90):ml[0]+90]=-1
    _,mx2,_,_=cv2.minMaxLoc(r)
    return float(mx),float(mx2),ml
for name,(x0,y0,x1,y1) in TPL.items():
    tpl=R[y0:y1,x0:x1]
    # ±10px 平移正样本：直接用原模板+稍大周边做平均不现实；按要求加平移变体匹配取峰
    line=[f"{name}:"]
    for tname,img in tests.items():
        best=(-1,None,None)
        for dx in (-10,-5,0,5,10):
            for dy in (-10,-5,0,5,10):
                x0t=max(0,x0+dx);y0t=max(0,y0+dy);x1t=min(905,x1+dx);y1t=min(550,y1+dy)
                tv=R[y0t:y1t,x0t:x1t]
                if tv.shape[:2]!=tpl.shape[:2]: continue
                p,s,ml=ncc_peak(img,tv)
                if p>best[0]: best=(p,s,ml)
        peak,second,ml=best
        ratio=peak/second if second>0 else 9.9
        verdict="认出" if peak>0.75 and ratio>1.5 else ("勉强" if peak>=0.6 else "认不出")
        line.append(f"{tname} peak={peak:.3f} second={second:.3f} ratio={ratio:.2f} @{ml} {verdict}")
    print(" | ".join(line))
