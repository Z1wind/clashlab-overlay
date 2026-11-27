# -*- coding: utf-8 -*-
"""v0.3.0：已放置建筑可用手指拖动调整格位。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
src = os.path.join(BASE, "android", "assets", "annotate9.html")
dst = os.path.join(BASE, "android", "assets", "annotate10.html")
t = open(src, encoding="utf-8").read()
t = t.replace("<h3>30 秒上手（v0.2.9）</h3>", "<h3>30 秒上手（v0.3.0）</h3>")

# 1) onDown: 靠近已放建筑 → 进入拖动
old_down = ("var p=screenToCanvas(ev),s=S();tapStart={x:p[0],y:p[1],cx:p[0],cy:p[1],moved:false,pan:false};\n"
            "  var ni=s.corners.length?nearestCorner(p[0],p[1]):-1;\n"
            "  if(ni>=0){dragIdx=ni;tapStart=null;toast('拖动第 '+(ni+1)+' 个角');return;}")
new_down = ("var p=screenToCanvas(ev),s=S();tapStart={x:p[0],y:p[1],cx:p[0],cy:p[1],moved:false,pan:false};\n"
            "  var ni=s.corners.length?nearestCorner(p[0],p[1]):-1;\n"
            "  if(ni>=0){dragIdx=ni;tapStart=null;toast('拖动第 '+(ni+1)+' 个角');return;}\n"
            "  if(s.corners.length===4&&s.buildings.length){var bi=nearestBuilding(p[0],p[1]);if(bi>=0){dragBld=bi;tapStart=null;toast('拖动建筑调整位置');return;}}")
if old_down in t:
    t = t.replace(old_down, new_down, 1); print("onDown patched")
else:
    print("onDown anchor miss")

# 2) onMove: 拖动建筑
old_move = "if(dragIdx>=0){var p=screenToCanvas(ev),s=S();"
new_move = ("if(dragBld>=0){var bp=screenToCanvas(ev),bs=S();var uv2=invBilinear(bp[0],bp[1]);"
            "var tx2=Math.round(uv2[0]*44-.5),ty2=Math.round(uv2[1]*44-.5);"
            "if(tx2>=0&&ty2>=0&&tx2<=43&&ty2<=43){bs.buildings[dragBld].tile=[tx2,ty2];draw();}return;}\n"
            "  if(dragIdx>=0){var p=screenToCanvas(ev),s=S();")
if old_move in t:
    t = t.replace(old_move, new_move, 1); print("onMove patched")
else:
    print("onMove anchor miss")

# 3) onUp: 结束建筑拖动
old_up = "if(dragIdx>=0){dragIdx=-1;saveLocal();updateUI();}"
new_up = ("if(dragBld>=0){dragBld=-1;saveLocal();updateUI();document.getElementById('tip').textContent=tipText();}"
          "if(dragIdx>=0){dragIdx=-1;saveLocal();updateUI();}")
if old_up in t:
    t = t.replace(old_up, new_up, 1); print("onUp patched")
else:
    print("onUp anchor miss")

# 4) 状态变量 + 命中函数
t = t.replace("var MARGIN=0.06, IMG={w:0,h:0,offX:0,offY:0};",
              "var MARGIN=0.06, IMG={w:0,h:0,offX:0,offY:0};var dragBld=-1;", 1)
anchor = "function nearestCorner(ix,iy){"
add = ("function nearestBuilding(ix,iy){var s=S(),best=-1,bd=26,i,d,cp;"
       "for(i=0;i<s.buildings.length;i++){cp=bil((s.buildings[i].tile[0]+.5)/44,(s.buildings[i].tile[1]+.5)/44);"
       "d=Math.hypot(cp[0]-ix,cp[1]-iy);if(d<bd){bd=d;best=i;}}return best;}\n")
t = t.replace(anchor, add + anchor, 1)
open(dst, "w", encoding="utf-8", newline="\n").write(t)
print("annotate10 written", len(t))
