# -*- coding: utf-8 -*-
# v14_extremes.py — 草地掩码极值点 + 角部标注。新文件。
import os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EN = os.path.join(ROOT, "out", "overlay", "enemy")

def grass_mask(im):
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    m = cv2.inRange(hsv, np.array([25, 25, 80]), np.array([85, 255, 255]))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((21,21),np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((11,11),np.uint8))
    # 去左上 UI 面板区
    m[0:260, 0:240] = 0
    m[600:720, 380:820] = 0  # 进攻按钮区
    return m

im = cv2.imdecode(np.fromfile(os.path.join(EN,"b14_ov1.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
m = grass_mask(im)
ys, xs = np.where(m>0)
# 极值：top 区域取 x 中位带
top_i = np.argmin(ys); bot_i = np.argmax(ys); lf_i = np.argmin(xs); rt_i = np.argmax(xs)
print("top", xs[top_i], ys[top_i], "bot", xs[bot_i], ys[bot_i], "L", xs[lf_i], ys[lf_i], "R", xs[rt_i], ys[rt_i])
vis = im.copy()
for name,(x,y) in {"T":(xs[top_i],ys[top_i]),"B":(xs[bot_i],ys[bot_i]),"L":(xs[lf_i],ys[lf_i]),"R":(xs[rt_i],ys[rt_i])}.items():
    cv2.circle(vis,(x,y),8,(0,0,255),2)
    cv2.putText(vis,f"{name}({x},{y})",(x+10,y),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,255),2)
cv2.imencode(".png",vis)[1].tofile(os.path.join(EN,"b14_extremes.png"))

# 四角标注裁块
def annot(src, box, name, step=10, scale=3.0):
    x1,y1,x2,y2 = box
    c = src[y1:y2, x1:x2].copy()
    for x in range(0,c.shape[1],step):
        cv2.line(c,(x,0),(x,c.shape[0]),(0,255,255),1)
        cv2.putText(c,str(x1+x),(x+1,12),cv2.FONT_HERSHEY_SIMPLEX,0.32,(0,255,255),1)
    for y in range(0,c.shape[0],step):
        cv2.line(c,(0,y),(c.shape[1],y),(0,255,255),1)
        cv2.putText(c,str(y1+y),(1,y+10),cv2.FONT_HERSHEY_SIMPLEX,0.32,(0,255,255),1)
    c = cv2.resize(c,None,fx=scale,fy=scale,interpolation=cv2.INTER_NEAREST)
    cv2.imencode(".png",c)[1].tofile(os.path.join(EN,name))

annot(im,(540,20,760,140),"b14_xT.png")
annot(im,(1030,280,1160,390),"b14_xR.png")
annot(im,(100,260,240,370),"b14_xL.png")
