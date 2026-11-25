# -*- coding: utf-8 -*-
# v14_final.py — b14 出图：修裁 full、叠格 grid、写 scale.json。新文件，不改旧文件。
import os, cv2, numpy as np, json, datetime
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EN = os.path.join(ROOT, "out", "overlay", "enemy")
im = cv2.imdecode(np.fromfile(os.path.join(EN,"b14_ov1.png"),dtype=np.uint8),cv2.IMREAD_COLOR)

T=(640,58); R=(1105,325); B=(640,600); L=(167,308)
W=R[0]-L[0]; H=B[1]-T[1]

# 1) 修裁 full：去左上奖励面板/底部进攻按钮与箭头/右下最佳进攻面板
CROP=(195,88,1065,582)
x1,y1,x2,y2=CROP
full=im[y1:y2,x1:x2]
cv2.imencode(".png",full)[1].tofile(os.path.join(EN,"b14_full.png"))

# 2) 44x44 双线性叠格（全帧坐标，再裁）
def bilin(u,v):
    a=u/44; b=v/44
    x=T[0]*(1-a)*(1-b)+R[0]*a*(1-b)+B[0]*a*b+L[0]*(1-a)*b
    y=T[1]*(1-a)*(1-b)+R[1]*a*(1-b)+B[1]*a*b+L[1]*(1-a)*b
    return int(round(x)),int(round(y))
grid=im.copy()
for u in range(0,45,1):
    p0=bilin(u,0); p1=bilin(u,44)
    cv2.line(grid,p0,p1,(0,255,255),1)
for v in range(0,45,1):
    p0=bilin(0,v); p1=bilin(44,v)
    cv2.line(grid,p0,p1,(0,255,255),1)
cv2.polylines(grid,[np.array([T,R,B,L],np.int32)],True,(0,0,255),2)
for nm,p in [("T",T),("R",R),("B",B),("L",L)]:
    cv2.circle(grid,p,6,(0,0,255),2)
g=grid[y1:y2,x1:x2]
cv2.imencode(".png",g)[1].tofile(os.path.join(EN,"b14_grid.png"))

# 3) scale.json
scale={
 "base":"b14_ov1.png (侦察预览全景,未缩放)",
 "quad":{"T":list(T),"R":list(R),"B":list(B),"L":list(L)},
 "W_px":W,"H_px":H,"H_W":round(H/W,3),"W_H":round(W/H,3),
 "px_per_tile":None,
 "px_per_tile_by":"quad44_projection",
 "px_per_tile_evidence":"无地面格线；全景分辨率下建筑底面轮廓不可辨(金仓/法师塔机身被围墙与邻舍遮挡,人工读数不可靠),未采信tool3(盟友帧consensus=False)。尺度由44x44已知平台投影反推: 双线性quad内嵌44x44格,格边长随投影各向异性,不在此报单一标量px/格; 叠格用bilinear映射。",
 "basis_projection":{"T_to_R":(R[0]-T[0],R[1]-T[1]),"L_to_R":(W, R[1]-L[1]),"T_to_B":(B[0]-T[0],H)},
 "canvas":[1280,720],
 "verts_in_canvas":{"T":True,"R":True,"B":False,"L":True,"note":"B(640,600)被底部进攻按钮UI覆盖,由两侧直边外推交点,未直接目视"},
 "occluded":[
   {"region":"底部中央 y600-700 x480-800","cause":"进攻!按钮UI覆盖","buildings":"底部中央条带1-2栋不可见(无法逐栋点名)"},
   {"region":"左上 x0-240 y0-260","cause":"奖励面板UI"},
   {"region":"右下 x1050-1280 y560-720","cause":"部落最佳进攻面板UI"}
 ],
 "camera":"free(pan自由,zoom pinch_zoom外扩有效/pinch_in_big可缩回全景;预览无格线)",
 "gridline_visible":False,
 "status":"near",
 "gap":"B角被进攻按钮遮挡未直读;建筑底面标尺在全景不可辨,尺度未独立直测,quad为人工+轮廓辅助读,H/W=1.731落在历史敌方1.697-1.826区间",
 "attack_button_tapped":False,
 "layout_modified":False,
 "ts":datetime.datetime.now().isoformat(timespec="seconds")
}
with open(os.path.join(EN,"b14_scale.json"),"w",encoding="utf-8") as f:
    json.dump(scale,f,ensure_ascii=False,indent=2)
print("W",W,"H",H,"W/H",round(W/H,3))
