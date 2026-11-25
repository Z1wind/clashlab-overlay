# -*- coding: utf-8 -*-
# v15_phase.py — 已有54块：相位相关估相邻平移，matchTemplate补，输出通过率与边表。新文件。
import os, cv2, numpy as np, json
R = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\_recon"
M = os.path.join(R,"max")
ROWS,COLS=9,6
def load(c,r):
    p=os.path.join(M,f"b_c{c}r{r}.png")
    return cv2.imdecode(np.fromfile(p,dtype=np.uint8),1)
# 中心大窗（去四周UI/徽章）
X0,X1,Y0,Y1=170,1110,275,605
def win(im):
    g=cv2.cvtColor(im[Y0:Y1,X0:X1],cv2.COLOR_BGR2GRAY).astype(np.float64)
    return g
def phase(a,b):
    ga,gb=win(a),win(b)
    h,w=ga.shape; winf=cv2.createHanningWindow((w,h),cv2.CV_64F)
    (dx,dy),resp=cv2.phaseCorrelate(ga,gb,winf)
    return float(dx),float(dy),float(resp)
def tmpl(a,b):
    # 取a靠边120px带（水平对取右带，垂直对取下带），由调用方传方向
    return None

imgs={(c,r):load(c,r) for r in range(ROWS) for c in range(COLS)}
edges=[];ok=0;tot=0
# 水平邻对
for r in range(ROWS):
    for c in range(COLS-1):
        a,b=imgs[(c,r)],imgs[(c+1,r)]
        dx,dy,resp=phase(a,b)
        method="phase";conf=False;reason=""
        if abs(dy)>5: reason=f"dy={dy:.1f}>5"
        elif not (100<=abs(dx)<=900): reason=f"|dx|={abs(dx):.1f} out"
        else: conf=True
        # matchTemplate 补
        if not conf:
            # a右带120px -> b内搜
            band=a[Y0:Y1,X1-120:X1]
            res=cv2.matchTemplate(b[Y0:Y1,X0:X1],band,cv2.TM_CCOEFF_NORMED)
            _,mx,_,loc=cv2.minMaxLoc(res)
            if mx>=0.6:
                # band在a中起点(X1-120)；匹配在b窗内loc，窗原点X0
                dx=loc[0]-(X1-120-X0); dy=0.0; method="tmpl"; conf=True; reason=f"tmpl {mx:.2f}"
            else: reason+=f" tmpl {mx:.2f}<0.6"
        tot+=1;ok+=conf
        edges.append({"dir":"h","a":[c,r],"b":[c+1,r],"dx":round(dx,1),"dy":round(dy,1),
                       "resp":round(resp,3),"method":method,"conf":conf,"reason":reason})
# 垂直邻对
for c in range(COLS):
    for r in range(ROWS-1):
        a,b=imgs[(c,r)],imgs[(c,r+1)]
        dx,dy,resp=phase(a,b)
        method="phase";conf=False;reason=""
        # 垂直对允许x漂移（行间列错位），只验dy模长与响应
        if not (100<=abs(dy)<=900): reason=f"|dy|={abs(dy):.1f} out"
        elif resp<0.02: reason=f"resp={resp:.3f}"
        else: conf=True
        if not conf:
            band=a[Y1-120:Y1,X0:X1]
            res=cv2.matchTemplate(b[Y0:Y1,X0:X1],band,cv2.TM_CCOEFF_NORMED)
            _,mx,_,loc=cv2.minMaxLoc(res)
            if mx>=0.6:
                dy=loc[1]-(Y1-120-Y0);dx=0.0;method="tmpl";conf=True;reason=f"tmpl {mx:.2f}"
            else: reason+=f" tmpl {mx:.2f}<0.6"
        tot+=1;ok+=conf
        edges.append({"dir":"v","a":[c,r],"b":[c,r+1],"dx":round(dx,1),"dy":round(dy,1),
                       "resp":round(resp,3),"method":method,"conf":conf,"reason":reason})
print(f"conf {ok}/{tot} = {100*ok/tot:.1f}%")
for e in edges:
    if not e["conf"]: print("FAIL",e["dir"],e["a"],"->",e["b"],e["dx"],e["dy"],e["reason"])
json.dump({"pass":ok,"total":tot,"rate":round(100*ok/tot,1),"edges":edges},
          open(os.path.join(R,"phase_edges.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
