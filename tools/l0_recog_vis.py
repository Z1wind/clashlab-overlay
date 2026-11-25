# -*- coding: utf-8 -*-
# 在 l0_A 与 pair 上画出匹配框+峰值，目检验证是否落在目标建筑
import cv2, numpy as np, os
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ref=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","ladder","zoom_L0.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
R=ref[80:630,155:1060]
TPL={
 "大本营":(560,220,645,305),
 "鹰炮":(375,275,460,360),
 "防空塔":(505,358,580,418),
 "金仓":(398,338,472,408),
 "法师塔":(505,338,580,408),
}
tests={
 "l0_A":cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","l0_A.png"),dtype=np.uint8),cv2.IMREAD_COLOR),
 "pair":cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_L0_pair_stitched.png"),dtype=np.uint8),cv2.IMREAD_COLOR),
}
colors=[(0,0,255),(0,255,0),(255,0,0),(0,255,255),(255,0,255)]
for tname,img in tests.items():
    vis=img.copy()
    for i,(name,(x0,y0,x1,y1)) in enumerate(TPL.items()):
        g=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY).astype(np.float32)
        t=cv2.cvtColor(R[y0:y1,x0:x1],cv2.COLOR_BGR2GRAY).astype(np.float32)
        res=cv2.matchTemplate(g,t,cv2.TM_CCOEFF_NORMED)
        _,mx,_,ml=cv2.minMaxLoc(res)
        cv2.rectangle(vis,ml,(ml[0]+(x1-x0),ml[1]+(y1-y0)),colors[i],2)
        cv2.putText(vis,f"{name} {mx:.2f}",(ml[0],ml[1]-6),cv2.FONT_HERSHEY_SIMPLEX,0.5,colors[i],2)
    cv2.imencode(".png",vis)[1].tofile(os.path.join(ROOT,"out","overlay",f"recog_{tname}.png"))
print("ok")
