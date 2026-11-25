# -*- coding: utf-8 -*-
# 同一金仓建筑 L3(近景) -> L0(全村) 多尺度模板匹配，求缩放比 -> tile_px_max
import cv2, numpy as np, os
D=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\ladder"
l0=cv2.imdecode(np.fromfile(os.path.join(D,"zoom_L0.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
l3=cv2.imdecode(np.fromfile(os.path.join(D,"zoom_L3.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
# L3 金仓区域
tpl=l3[380:560,150:360]
best=None
for sc in np.arange(2.0,6.0,0.05):
    th,tw=int(tpl.shape[0]*sc),int(tpl.shape[1]*sc)
    big=cv2.resize(l0,(int(l0.shape[1]*sc),int(l0.shape[0]*sc)),interpolation=cv2.INTER_CUBIC)
    if th>big.shape[0] or tw>big.shape[1]: break
    res=cv2.matchTemplate(big,tpl,cv2.TM_CCOEFF_NORMED)
    _,mv,_,ml=cv2.minMaxLoc(res)
    if best is None or mv>best[0]: best=(mv,sc,ml)
print("best corr=%.3f scale(L3/L0)=%.2f at %s"%(best[0],best[1],best[2]))
# L0 tile_px=24.0 -> L3 tile_px = 24/scale
print("L3 tile_px = %.2f px"%(24.0/best[1]))
