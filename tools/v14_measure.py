# -*- coding: utf-8 -*-
# v14_measure.py — ov1 上已知建筑底面标注裁块，人工量 px 跨度。新文件。
import os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EN = os.path.join(ROOT, "out", "overlay", "enemy")
im = cv2.imdecode(np.fromfile(os.path.join(EN,"b14_ov1.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
def annot(box,name,step=10,scale=3.0):
    x1,y1,x2,y2=box
    c=im[y1:y2,x1:x2].copy()
    for x in range(0,c.shape[1],step):
        cv2.line(c,(x,0),(x,c.shape[0]),(0,255,255),1)
        cv2.putText(c,str(x1+x),(x+1,11),cv2.FONT_HERSHEY_SIMPLEX,0.3,(0,255,255),1)
    for y in range(0,c.shape[0],step):
        cv2.line(c,(0,y),(c.shape[1],y),(0,255,255),1)
        cv2.putText(c,str(y1+y),(1,y+9),cv2.FONT_HERSHEY_SIMPLEX,0.3,(0,255,255),1)
    c=cv2.resize(c,None,fx=scale,fy=scale,interpolation=cv2.INTER_NEAREST)
    cv2.imencode(".png",c)[1].tofile(os.path.join(EN,name))
annot((560,290,730,430),"m_th.png",10,2.6)       # TH 4x4
annot((700,210,850,330),"m_goldNE.png",10,3.0)   # 金仓?
annot((350,290,490,400),"m_wizNW.png",10,3.0)
annot((860,290,1000,400),"m_wizNE.png",10,3.0)
annot((350,440,490,550),"m_goldSW.png",10,3.0)
annot((790,440,930,550),"m_goldSE.png",10,3.0)
print("ok")
