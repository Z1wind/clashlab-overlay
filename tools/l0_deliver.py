# -*- coding: utf-8 -*-
# Step3交付：base原图 / quad反投影44x44网格 / 候选命中标注
import cv2, numpy as np, os, json
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT=os.path.join(ROOT,"out","overlay","l0new")
base=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_l0_two_shot_base.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
cfg=json.load(open(os.path.join(ROOT,"config","view_quads.json"),encoding="utf-8"))
q=cfg["quad"]; T=np.array(q["T"]);R=np.array(q["R"]);B=np.array(q["B"]);L=np.array(q["L"])
H,W=base.shape[:2]

# --- 44x44网格：quad(T,R,B,L) -> 单位正方形(0,0),(44,0),(44,44),(0,44) ---
src=np.float32([T,R,B,L])
dst=np.float32([[0,0],[44,0],[44,44],[0,44]])
M=cv2.getPerspectiveTransform(dst,src)  # 单位网格 -> 画布
grid=base.copy()
# 在单位正方形画45条竖线+45条横线，warp到画布
pad=60
canvas_g=np.zeros((H+2*pad,W+2*pad,3),np.uint8)
unit=np.zeros((440,440),np.uint8)
for i in range(45):
    cv2.line(unit,(i*10,0),(i*10,440),255,1)
    cv2.line(unit,(0,i*10),(440,i*10),255,1)
# 单位->画布 M作用在(0..44,0..44)
for i in range(45):
    p1=M@np.array([i/44*44,0,1]); p2=M@np.array([i/44*44,44,1])
    p1/=p1[2]; p2/=p2[2]
    cv2.line(grid,(int(p1[0])+pad-60,int(p1[1])+pad-60),(int(p2[0])+pad-60,int(p2[1])+pad-60),(0,0,255),1)
    q1=M@np.array([0,i/44*44,1]); q2=M@np.array([44,i/44*44,1])
    q1/=q1[2]; q2/=q2[2]
    cv2.line(grid,(int(q1[0]),int(q1[1])),(int(q2[0]),int(q2[1])),(0,0,255),1)
cv2.imencode(".png",grid)[1].tofile(os.path.join(ROOT,"out","overlay","v6_l0_grid_aligned.png"))

# --- marks：候选命中(recog_cross.json) 标注 ---
rec=json.load(open(os.path.join(OUT,"recog_cross.json"),encoding="utf-8"))
marks=base.copy()
colors={"大本营":(0,255,0),"鹰炮":(255,0,255),"防空塔":(255,0,0),"金仓":(0,165,255),"法师塔":(255,255,0)}
for name,d in rec.items():
    for mv,px,py in d["peaks"]:
        cx,cy=px+35,py+40
        cv2.circle(marks,(cx,cy),12,colors[name],2)
        cv2.putText(marks,f"{name} {mv:.2f}",(cx+14,cy-8),cv2.FONT_HERSHEY_SIMPLEX,0.45,colors[name],2)
cv2.imencode(".png",marks)[1].tofile(os.path.join(ROOT,"out","overlay","v6_l0_marks.png"))
print("saved grid + marks")
