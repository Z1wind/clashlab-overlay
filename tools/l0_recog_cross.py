# -*- coding: utf-8 -*-
# 跨帧NCC：A帧抠模板(由ref模板盒经ORB平移映射) -> B帧重叠带多峰搜索
# 判据 peak>0.75；NMS屏蔽90px；报每座坐标/置信；命中座数 vs 应有座数
import cv2, numpy as np, os, json
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT=os.path.join(ROOT,"out","overlay","l0new")
A=cv2.imdecode(np.fromfile(os.path.join(OUT,"A.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
B=cv2.imdecode(np.fromfile(os.path.join(OUT,"B.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
ref=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","ladder","zoom_L0.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
refc=ref[80:630,155:1105]
# ORB A->ref 平移
orb=cv2.ORB_create(1500)
ka,da=orb.detectAndCompute(cv2.cvtColor(A,cv2.COLOR_BGR2GRAY),None)
kb,db=orb.detectAndCompute(cv2.cvtColor(refc,cv2.COLOR_BGR2GRAY),None)
bf=cv2.BFMatcher(cv2.NORM_HAMMING)
good=[m for m,n in bf.knnMatch(da,db,k=2) if m.distance<0.75*n.distance]
pa=np.float32([ka[m.queryIdx].pt for m in good]); pb=np.float32([kb[m.trainIdx].pt for m in good])
d=pb-pa; mx,my=np.median(d,axis=0)
inl=np.linalg.norm(d-[mx,my],axis=1)<15
print("A->ref shift=",mx,my,"inl=",int(inl.sum()),"/",len(good))
# ref模板盒(refc坐标, 950宽)
TPL={
 "大本营":(560,220,645,305,1),
 "鹰炮":(375,275,460,360,4),
 "防空塔":(505,358,580,418,4),
 "金仓":(398,338,472,408,4),
 "法师塔":(505,338,580,408,3),
}
# B重叠带: A底部327px对应B顶部327px
band=B[:328,:]
results={}
vis=B.copy()
for name,(x0,y0,x1,y1,expect) in TPL.items():
    # 映射到A坐标: A点+shift = ref点 => A盒 = ref盒 - shift
    ax0=int(round(x0-mx)); ay0=int(round(y0-my)); ax1=int(round(x1-mx)); ay1=int(round(y1-my))
    tpl=None
    if 0<=ax0 and ay0>=0 and ax1<=A.shape[1] and ay1<=A.shape[0]:
        tpl=A[ay0:ay1,ax0:ax1]
        src="A"
    else:
        tpl=refc[y0:y1,x0:x1]; src="ref(fallback)"
    g=cv2.cvtColor(band,cv2.COLOR_BGR2GRAY).astype(np.float32)
    t=cv2.cvtColor(tpl,cv2.COLOR_BGR2GRAY).astype(np.float32)
    res=cv2.matchTemplate(g,t,cv2.TM_CCOEFF_NORMED)
    # 多峰NMS
    peaks=[]
    r=res.copy()
    while True:
        _,mv,_,ml=cv2.minMaxLoc(r)
        if mv<0.75: break
        peaks.append((float(mv),int(ml[0]),int(ml[1])))
        cv2.rectangle(r,(ml[0]-90,ml[1]-90),(ml[0]+90,ml[1]+90),-1,-1)
    results[name]={"expect":expect,"src":src,"peaks":peaks}
    print(f"\n{name} (应有{expect}座, 模板{src})")
    for p in peaks:
        print(f"  peak={p[0]:.3f} @(x{p[1]},y{p[2]})")
        cv2.circle(vis,(p[1]+t.shape[1]//2,p[2]+t.shape[0]//2),10,(0,0,255),2)
        cv2.putText(vis,name,(p[1],p[2]-6),cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,0,255),1)
cv2.imencode(".png",vis)[1].tofile(os.path.join(OUT,"recog_cross.png"))
json.dump(results,open(os.path.join(OUT,"recog_cross.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
