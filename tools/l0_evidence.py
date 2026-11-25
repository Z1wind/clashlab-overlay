# -*- coding: utf-8 -*-
# 纯离线：①证据图(5处机身跨度标注) + ②证据图复核
import cv2, numpy as np, os
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
im=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_l0_three_shot_base.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
# ① 跨度标注(视觉,沿机身轴)
SPANS=[
 ("金仓NE",(498,178),(568,206)),
 ("金仓SW",(178,578),(248,606)),
 ("金仓SE",(614,616),(686,640)),
 ("金仓S",(370,726),(440,758)),
 ("法师塔SE",(627,646),(693,678)),
]
v1=im.copy()
for nm,p,q in SPANS:
    cv2.line(v1,p,q,(0,0,255),2)
    cv2.putText(v1,nm,((p[0]+q[0])//2-30,(p[1]+q[1])//2-8),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,0,255),2)
cv2.imencode(".png",v1)[1].tofile(os.path.join(ROOT,"out","overlay","l0three","footprint_evidence.png"))
# ② 复核已有 measure_evidence.png
print("saved footprint_evidence.png")
