# -*- coding: utf-8 -*-
"""v0.2.7：拖角到画布边缘时自动平移视图，实现四角无限越界。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "android", "assets", "annotate7.html")
t = open(p, encoding="utf-8").read()
old = "s.corners[dragIdx]=[Math.max(-0.25,Math.min(1.25,(p[0]-IMG.offX)/IMG.w)),Math.max(-0.25,Math.min(1.25,(p[1]-IMG.offY)/IMG.h))];draw();return;"
new = ("var EDGE=40,STEP=6,moved=false;"
       "if(p[0]<EDGE){view.panX+=STEP;moved=true;}else if(p[0]>cv.width-EDGE){view.panX-=STEP;moved=true;}"
       "if(p[1]<EDGE){view.panY+=STEP;moved=true;}else if(p[1]>cv.height-EDGE){view.panY-=STEP;moved=true;}"
       "if(moved){draw();p=screenToCanvas(ev);}"
       "s.corners[dragIdx]=[Math.max(-0.6,Math.min(1.6,(p[0]-IMG.offX)/IMG.w)),Math.max(-0.6,Math.min(1.6,(p[1]-IMG.offY)/IMG.h))];draw();return;")
if old in t:
    t = t.replace(old, new, 1)
    t = t.replace("Math.max(-0.25,Math.min(1.25,(ix-IMG.offX)/IMG.w)),Math.max(-0.25,Math.min(1.25,(iy-IMG.offY)/IMG.h))",
                  "Math.max(-0.6,Math.min(1.6,(ix-IMG.offX)/IMG.w)),Math.max(-0.6,Math.min(1.6,(iy-IMG.offY)/IMG.h))", 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("auto-pan patched", len(t))
else:
    print("anchor miss")
