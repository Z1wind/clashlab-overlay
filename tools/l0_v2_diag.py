# -*- coding: utf-8 -*-
# 纯离线诊断(非真值)：v2 反算在38个手工锚点上的余量px/格，对比v1；仅作量级参考
import cv2, numpy as np, os, math, json
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
# 38锚点(来自 l0_snap_calib.py / l0_snap_final.py ANCHORS，仅诊断，不作真值)
ANCHORS=[
 ("选择木屋",235,175),("紫圣水罐T",415,175),("黑紫建筑",290,250),
 ("金仓黄圆NW",240,285),("紫圣水W",195,300),("金堆NW",355,335),
 ("紫塔W",165,385),("金仓黄圆W2",105,395),("紫圣水W2",105,455),
 ("金仓黄圆NE",505,150),("紫圣水NE",610,265),("紫塔NE",650,270),
 ("黑罐NE",710,300),("金堆NE",670,355),("黑炮熔炉",265,290),
 ("黑塔N",330,285),("黑塔C",345,405),("中央暗黑大塔",415,455),
 ("金仓黄圆SW1",185,565),("紫圣水SW",215,580),("紫圣水E",620,275),
 ("黑罐E",715,300),("橙熔炉E",660,320),("深色储物E",555,365),
 ("黑塔E",640,375),("大本营",600,490),("紫圣水SE",815,545),
 ("黑罐SE",705,590),("金仓黄圆SE",610,605),("金仓黄圆SW2",175,555),
 ("橙熔炉SW",275,600),("黑炮SW",320,665),("金仓黄圆S",400,720),
 ("黑罐S",595,575),("金仓黄圆S2",550,600),("紫塔S",595,635),
 ("紫圣水S2",510,715),("黑炮S2",555,715),
]
def inv_factory(O,a,b):
    M=np.column_stack([a,b]); Mi=np.linalg.inv(M)
    return lambda p:(np.array(p)-O)@Mi.T
# v2
v2=inv_factory(np.array([473.2,796.6]),np.array([11.787,20.906]),np.array([-20.337,12.744]))
# v1
v1=inv_factory(np.array([473.2,796.6]),np.array([13.17,23.36]),np.array([-20.06,12.57]))
rows=[]
for nm,x,y in ANCHORS:
    ij2=v2((x,y)); ij1=v1((x,y))
    d2=np.linalg.norm(ij2-np.round(ij2)); d1=np.linalg.norm(ij1-np.round(ij1))
    # v2 像素余量 = 到最近格点欧氏距离(近似24*d2)
    rows.append((nm,x,y,ij2,d2,ij1,d1))
ds2=[r[4] for r in rows]; ds1=[r[6] for r in rows]
print("=== v2 @ anchors (diagnostic, NOT truth) ===")
print(f"v2 mean residual {np.mean(ds2):.3f}格 max {max(ds2):.3f}格  (px@24: mean {np.mean(ds2)*24:.1f} max {max(ds2)*24:.1f})")
print(f"v1 mean residual {np.mean(ds1):.3f}格 max {max(ds1):.3f}格")
for r in rows:
    print(f"{r[0]:10s} v2 ij=({r[3][0]:6.2f},{r[3][1]:6.2f}) d={r[4]:.3f}  v1 d={r[6]:.3f}")
