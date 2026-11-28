# -*- coding: utf-8 -*-
"""修复：单击放点 vs 拖动平移（拖动超过阈值才平移）。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "android", "assets", "annotate10.html")
t = open(p, encoding="utf-8").read()
# 1) onDown 不再直接进入平移
old_down = "  if(view.scale>1.01){tapStart.pan=true;}"
if old_down in t:
    t = t.replace(old_down, "  tapStart.pan=false;", 1); print("onDown fixed")
else:
    # HTML 版可能已被改为无条件
    old2 = "  tapStart.pan=true;"
    if old2 in t:
        t = t.replace(old2, "  tapStart.pan=false;", 1); print("onDown fixed(alt)")
    else:
        print("onDown anchor miss")
# 2) onMove：超过阈值才进入平移
old_move = ("  if(!tapStart||!tapStart.pan)return;\n"
            "  var r=cv.getBoundingClientRect();var sx=(raw.clientX-r.left)*(cv.width/r.width);var sy=(raw.clientY-r.top)*(cv.height/r.height);\n"
            "  if(Math.abs(sx-tapStart.cx)+Math.abs(sy-tapStart.cy)>8){tapStart.moved=true;}\n"
            "  if(tapStart.moved){view.panX+= (sx-tapStart.cx)*1;view.panY+=(sy-tapStart.cy)*1;tapStart.cx=sx;tapStart.cy=sy;draw();}")
new_move = ("  if(!tapStart)return;\n"
            "  var r=cv.getBoundingClientRect();var sx=(raw.clientX-r.left)*(cv.width/r.width);var sy=(raw.clientY-r.top)*(cv.height/r.height);\n"
            "  if(Math.abs(sx-tapStart.cx)+Math.abs(sy-tapStart.cy)>6){tapStart.moved=true;}\n"
            "  if(tapStart.moved){tapStart.pan=true;view.panX+=(sx-tapStart.cx);view.panY+=(sy-tapStart.cy);tapStart.cx=sx;tapStart.cy=sy;draw();}")
if old_move in t:
    t = t.replace(old_move, new_move, 1); print("onMove fixed")
else:
    print("onMove anchor miss")
# 3) onUp：只要没拖动就触发点击
old_up = "  if(tapStart&&!tapStart.moved&&!tapStart.pan){var r=cv.getBoundingClientRect();if(!maybeDoubleTap(tapStart.x,tapStart.y))doTap(tapStart.x,tapStart.y);}"
new_up = "  if(tapStart&&!tapStart.moved){if(!maybeDoubleTap(tapStart.x,tapStart.y))doTap(tapStart.x,tapStart.y);}"
if old_up in t:
    t = t.replace(old_up, new_up, 1); print("onUp fixed")
else:
    print("onUp anchor miss")
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("annotate10 patched", len(t))
