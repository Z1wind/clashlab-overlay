# -*- coding: utf-8 -*-
# 用wall-ring quad透视反投影画44x44；输出grid图供目检
import cv2, numpy as np, os, json
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
im=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_l0_three_shot_base.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
q=json.load(open(os.path.join(ROOT,"out","overlay","l0three","quad_wall.json"),encoding="utf-8"))
T=np.array(q["T"]);R=np.array(q["R"]);B=np.array(q["B"]);L=np.array(q["L"])
src=np.float32([T,R,B,L]); dst=np.float32([[0,0],[44,0],[44,44],[0,44]])
M=cv2.getPerspectiveTransform(dst,src)
grid=im.copy()
for i in range(45):
    p1=M@np.array([i,0,1]); p2=M@np.array([i,44,1]); p1/=p1[2];p2/=p2[2]
    cv2.line(grid,(int(p1[0]),int(p1[1])),(int(p2[0]),int(p2[1])),(0,0,255),1)
    q1=M@np.array([0,i,1]); q2=M@np.array([44,i,1]); q1/=q1[2];q2/=q2[2]
    cv2.line(grid,(int(q1[0]),int(q1[1])),(int(q2[0]),int(q2[1])),(0,0,255),1)
cv2.imencode(".png",grid)[1].tofile(os.path.join(ROOT,"out","overlay","v6_l0_grid_aligned.png"))
print("grid drawn")
