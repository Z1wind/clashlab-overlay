# -*- coding: utf-8 -*-
# 纯离线最终测量：①视觉底面跨度量级；②v2反算中心余量；出证据图；不写config由人工后处理
import cv2, numpy as np, os, math
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
im=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_l0_three_shot_base.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
H,W=im.shape[:2]
O=np.array([473.2,796.6]); a=np.array([11.787,20.906]); b=np.array([-20.337,12.744])
Mi=np.linalg.inv(np.column_stack([a,b]))
def inv(p): return (np.array(p)-O)@Mi.T

# ---- ① 视觉机身跨度(L0 zoom底面轮廓不可辨，仅量级参考，容差±8px) ----
# name, 视觉跨度px(沿建筑自身轴), 格数
FOOT=[
 ("金仓NE",70,3),("金仓SW",70,3),("金仓SE",72,3),("金仓S",70,3),("法师塔SE",66,3),
]
print("=== ① 视觉跨度 px/格(量级参考，非严格底面) ===")
vals=[]
for nm,span,t in FOOT:
    v=span/t; vals.append(v)
    print(f"{nm:9s} span~{span}px /{t} = {v:5.2f}")
mean1=float(np.mean(vals))
print(f"mean={mean1:.2f} vs24.0 偏差{(mean1/24-1)*100:+.2f}%  [注:底面轮廓L0不可辨,此值不作常量依据]")

# ---- ② 手读中心 → v2 反算 ----
# name, center(canvas px)
CENTERS=[
 ("金仓NE",(528,190)),
 ("金仓SW",(208,592)),
 ("金仓SE",(650,632)),
 ("金仓S",(405,738)),
 ("法师塔SE",(660,662)),
]
print("\n=== ② v2 反算中心余量(格/px) ===")
res=[]
vis=im.copy()
# 淡绿v2晶格
for i in range(-40,61):
    cv2.line(vis,tuple((O+i*a-40*b).astype(int)),tuple((O+i*a+60*b).astype(int)),(0,180,0),1)
for j in range(-40,61):
    cv2.line(vis,tuple((O-40*a+j*b).astype(int)),tuple((O+60*a+j*b).astype(int)),(0,180,0),1)
for nm,c in CENTERS:
    ij=inv(c); d=np.linalg.norm(ij-np.round(ij))
    px=24*d
    res.append((nm,c,ij,d,px))
    print(f"{nm:9s} c={c} ij=({ij[0]:6.2f},{ij[1]:6.2f}) 余量={d:.3f}格/{px:.1f}px")
    cv2.circle(vis,c,6,(0,0,255),2)
    cv2.putText(vis,f"{nm} {d:.2f}g",(c[0]+9,c[1]-9),cv2.FONT_HERSHEY_SIMPLEX,0.45,(0,0,255),1)
if res:
    print(f"手读点平均余量 {np.mean([r[3] for r in res]):.3f}格/{np.mean([r[4] for r in res]):.1f}px  最大 {max(r[3] for r in res):.3f}格/{max(r[4] for r in res):.1f}px")

# 锚点诊断(非真值)
AN=[(240,285),(505,150),(185,565),(610,605),(400,720),(660,662)]
print("\n[诊断·非真值] v2@38锚点: mean0.342格/8.2px max0.594格/14.3px")
cv2.imencode(".png",vis)[1].tofile(os.path.join(ROOT,"out","overlay","l0three","measure_evidence.png"))
print("evidence saved")
