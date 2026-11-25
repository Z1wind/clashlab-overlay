# -*- coding: utf-8 -*-
# 终稿: 跨帧NCC候选 -> marks; 写view_quads.json(含FAIL标记)
import cv2, numpy as np, os, json, time
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT=os.path.join(ROOT,"out","overlay","l0three")
base=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_l0_three_shot_base.png"),dtype=np.uint8),cv2.IMREAD_COLOR)[:, :905]
cv2.imencode(".png",cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_l0_three_shot_base.png"),dtype=np.uint8),cv2.IMREAD_COLOR)[:, :905])[1].tofile(os.path.join(ROOT,"out","overlay","v6_l0_three_shot_base.png"))
f0=cv2.imdecode(np.fromfile(os.path.join(OUT,"f0.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
f1=cv2.imdecode(np.fromfile(os.path.join(OUT,"f1.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
f2=cv2.imdecode(np.fromfile(os.path.join(OUT,"f2.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
ref=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","ladder","zoom_L0.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
refc=ref[80:630,155:1105]
orb=cv2.ORB_create(1500)
def shift(a,b):
    ka,da=orb.detectAndCompute(cv2.cvtColor(a,cv2.COLOR_BGR2GRAY),None)
    kb,db=orb.detectAndCompute(cv2.cvtColor(b,cv2.COLOR_BGR2GRAY),None)
    bf=cv2.BFMatcher(cv2.NORM_HAMMING)
    good=[m for m,n in bf.knnMatch(da,db,k=2) if m.distance<0.75*n.distance]
    pa=np.float32([ka[m.queryIdx].pt for m in good]); pb=np.float32([kb[m.trainIdx].pt for m in good])
    d=pb-pa; mx,my=np.median(d,axis=0)
    return mx,my
sx,sy=shift(f0,refc)
TPL={"大本营":(560,220,645,305,1),"鹰炮":(375,275,460,360,4),"防空塔":(505,358,580,418,4),"金仓":(398,338,472,408,4),"法师塔":(505,338,580,408,3)}
chain=[f1,f2]
marks=base.copy()
report={}
for name,(x0,y0,x1,y1,expect) in TPL.items():
    ax0=int(round(x0-sx));ay0=int(round(y0-sy));ax1=int(round(x1-sx));ay1=int(round(y1-sy))
    tpl=f0[ay0:ay1,ax0:ax1] if 0<=ax0 and ay0>=0 and ax1<=f0.shape[1] and ay1<=f0.shape[0] else refc[y0:y1,x0:x1]
    peaks=[]
    for fr,yo in [(f1,259.75),(f2,517.92)]:
        g=cv2.cvtColor(fr,cv2.COLOR_BGR2GRAY).astype(np.float32)
        t=cv2.cvtColor(tpl,cv2.COLOR_BGR2GRAY).astype(np.float32)
        res=cv2.matchTemplate(g,t,cv2.TM_CCOEFF_NORMED)
        r=res.copy()
        while True:
            _,mv,_,ml=cv2.minMaxLoc(r)
            if mv<0.75: break
            peaks.append((float(mv),int(ml[0]),int(ml[1])+yo))
            cv2.rectangle(r,(ml[0]-90,ml[1]-90),(ml[0]+90,ml[1]+90),-1,-1)
    report[name]={"expect":expect,"peaks":peaks}
    for mv,px,py in peaks:
        cv2.circle(marks,(int(px+35),int(py+40)),10,(120,120,120),2)
        cv2.putText(marks,f"{name}?{mv:.2f}",(int(px+48),int(py+32)),cv2.FONT_HERSHEY_SIMPLEX,0.4,(120,120,120),1)
    print(name,"expect",expect,"peaks",[(round(p[0],3),p[1],p[2]) for p in peaks])
cv2.imencode(".png",marks)[1].tofile(os.path.join(ROOT,"out","overlay","v6_l0_marks.png"))
qw=json.load(open(os.path.join(OUT,"quad_wall.json"),encoding="utf-8"))
cfg={"quad":qw,"canvas":[950,1068],"canvas_tiles":[39.6,44.5],"tile_px":24.0,"tile_px_range":[23.8,24.4],
 "source":"L0_three_shot+wall_ring_fit","shots":3,"overlap_tiles":[12.1,12.1],
 "seam_resid":[0.040,0.036],
 "fit_resid":qw["resid"],
 "HW_check":{"value":qw["HW"],"target":"0.5±0.10","PASS":bool(abs(qw["HW"]-0.5)<=0.10),"note":"围墙环H/W=1.324不达标,边族聚类混入内圈墙,quad不验收"},
 "vertices_inside":qw["inside"],
 "recognition":report,
 "ts":time.strftime("%Y-%m-%dT%H:%M:%S")}
os.makedirs(os.path.join(ROOT,"config"),exist_ok=True)
json.dump(cfg,open(os.path.join(ROOT,"config","view_quads.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print("done")
