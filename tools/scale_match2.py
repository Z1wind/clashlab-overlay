# -*- coding: utf-8 -*-
# 模板缩小匹配：L3金仓 -> L0，scale = tpl/L0 大小比；tile_px_L3=24*scale
import cv2, numpy as np, os
D=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\ladder"
l0=cv2.imdecode(np.fromfile(os.path.join(D,"zoom_L0.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
l3=cv2.imdecode(np.fromfile(os.path.join(D,"zoom_L3.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
tpl=l3[380:560,150:360]
best=None
for s in np.arange(0.10,0.55,0.01):
    th,tw=max(8,int(tpl.shape[0]*s)),max(8,int(tpl.shape[1]*s))
    small=cv2.resize(tpl,(tw,th),interpolation=cv2.INTER_AREA)
    if th>l0.shape[0] or tw>l0.shape[1]: continue
    res=cv2.matchTemplate(l0,small,cv2.TM_CCOEFF_NORMED)
    _,mv,_,ml=cv2.minMaxLoc(res)
    if best is None or mv>best[0]: best=(mv,s,ml)
print("corr=%.3f tpl/L0 scale=%.3f loc=%s"%(best[0],best[1],best[2]))
print("L3 tile_px = 24 * %.3f = %.2f"%(best[1],24*best[1]))
# 同样测 L1
t1=cv2.imdecode(np.fromfile(os.path.join(D,"zoom_L1.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
# L1 中央城堡区裁块作模板
tpl1=t1[250:430,300:480]
best1=None
for s in np.arange(0.15,0.7,0.01):
    th,tw=max(8,int(tpl1.shape[0]*s)),max(8,int(tpl1.shape[1]*s))
    small=cv2.resize(tpl1,(tw,th),interpolation=cv2.INTER_AREA)
    if th>l0.shape[0] or tw>l0.shape[1]: continue
    res=cv2.matchTemplate(l0,small,cv2.TM_CCOEFF_NORMED)
    _,mv,_,ml=cv2.minMaxLoc(res)
    if best1 is None or mv>best1[0]: best1=(mv,s,ml)
print("L1: corr=%.3f scale=%.3f tile_px=%.2f"%(best1[0],best1[1],24*best1[1]))
