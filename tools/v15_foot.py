# -*- coding: utf-8 -*-
# v15_foot.py — 给定帧+人工框，分割紫瓶(金/水仓)色掩码，报 rhombus 水平宽/垂直高，反推 a 与 |east|。
# 用法: python v15_foot.py <frame> <box,x1,y1,x2,y2> <n>
import sys, os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EN = os.path.join(ROOT, "out", "overlay", "enemy")
frame = sys.argv[1]; box = [int(v) for v in sys.argv[2].split(",")]; n = int(sys.argv[3])
im = cv2.imdecode(np.fromfile(os.path.join(EN,frame),dtype=np.uint8),cv2.IMREAD_COLOR)
x1,y1,x2,y2 = box
crop = im[y1:y2, x1:x2]
hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
# 紫瓶：紫/品红 高饱和
m = cv2.inRange(hsv, np.array([120,60,60]), np.array([175,255,255])) | \
    cv2.inRange(hsv, np.array([0,60,60]), np.array([10,255,255]))
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7,7),np.uint8))
cnts,_ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
if not cnts:
    print("no mask"); sys.exit()
c = max(cnts,key=cv2.contourArea)
bx,by,bw,bh = cv2.boundingRect(c)
vis = crop.copy(); cv2.drawContours(vis,[c],-1,(0,0,255),2)
cv2.rectangle(vis,(bx,by),(bx+bw,by+bh),(0,255,0),2)
cv2.imencode(".png",vis)[1].tofile(os.path.join(EN,"foot_debug.png"))
# n×n rhombus: 水平宽=2n*a, 垂直高=2n*b, b=a/1.732(iso30)
a = bw/(2*n)
east = a*np.sqrt(1+1/3)   # |east|=sqrt(a^2+b^2)
print(f"bw={bw} bh={bh} a={a:.1f} |east|={east:.1f} (n={n})")
