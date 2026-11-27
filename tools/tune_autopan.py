# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "android", "assets", "annotate7.html")
t = open(p, encoding="utf-8").read()
old = "var EDGE=40,STEP=6,moved=false;"
new = "var EDGE=36,STEP=2,moved=false;"
t = t.replace(old, new, 1)
old2 = "if(moved){draw();p=screenToCanvas(ev);}"
new2 = ("view.panX=Math.max(-IMG.w*0.8,Math.min(IMG.w*0.8,view.panX));"
        "view.panY=Math.max(-IMG.h*0.8,Math.min(IMG.h*0.8,view.panY));"
        "if(moved){draw();p=screenToCanvas(ev);}")
t = t.replace(old2, new2, 1)
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("STEP=2 cap patched", len(t))
