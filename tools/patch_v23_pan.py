# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "android", "assets", "annotate4.html")
t = open(p, encoding="utf-8").read()
old_start = "function onDown(ev){ev.preventDefault();"
old_end = "cv.addEventListener('mousedown',onDown);"
i = t.index(old_start); j = t.index(old_end)
new = '''function onDown(ev){ev.preventDefault();
  if(ev.touches&&ev.touches.length>=2){var a=ev.touches[0],b=ev.touches[1];pinch={d:Math.hypot(a.clientX-b.clientX,a.clientY-b.clientY),scale:view.scale};dragIdx=-1;tapStart=null;return;}
  var p=screenToCanvas(ev),s=S();tapStart={x:p[0],y:p[1],cx:p[0],cy:p[1],moved:false,pan:false};
  var ni=s.corners.length?nearestCorner(p[0],p[1]):-1;
  if(ni>=0){dragIdx=ni;tapStart=null;toast('拖动第 '+(ni+1)+' 个角');return;}
  if(view.scale>1.01){tapStart.pan=true;}
}
function onMove(ev){ev.preventDefault();
  if(pinch&&ev.touches&&ev.touches.length>=2){var a=ev.touches[0],b=ev.touches[1];var d=Math.hypot(a.clientX-b.clientX,a.clientY-b.clientY);view.scale=Math.max(1,Math.min(6,pinch.scale*d/pinch.d));draw();return;}
  var raw=(ev.touches&&ev.touches[0])?ev.touches[0]:ev;
  if(dragIdx>=0){var p=screenToCanvas(ev),s=S();s.corners[dragIdx]=[Math.max(0,Math.min(1,p[0]/cv.width)),Math.max(0,Math.min(1,p[1]/cv.height))];draw();return;}
  if(!tapStart||!tapStart.pan)return;
  var r=cv.getBoundingClientRect();var sx=(raw.clientX-r.left)*(cv.width/r.width);var sy=(raw.clientY-r.top)*(cv.height/r.height);
  if(Math.abs(sx-tapStart.cx)+Math.abs(sy-tapStart.cy)>8){tapStart.moved=true;}
  if(tapStart.moved){view.panX+= (sx-tapStart.cx)*1;view.panY+=(sy-tapStart.cy)*1;tapStart.cx=sx;tapStart.cy=sy;draw();}
}
function doTap(ix,iy){
  var s=S();
  if(s.corners.length<4){s.corners.push([Math.max(0,Math.min(1,ix/cv.width)),Math.max(0,Math.min(1,iy/cv.height))]);
    if(s.corners.length===4){toast('标定完成，选建筑类型再点建筑');document.getElementById('hint').textContent='② 选建筑 → ③ 点建筑（黄点可拖，双指缩放）';}draw();updateUI();saveLocal();return;}
  var uv=invBilinear(ix,iy);var tx=Math.round(uv[0]*44-.5),ty=Math.round(uv[1]*44-.5);
  if(tx<0||ty<0||tx>43||ty>43){toast('点在基地外了，往里点');return;}
  var hit=hitExisting([tx,ty]);if(hit>=0){s.buildings.splice(hit,1);toast('已删除');}else{s.buildings.push({type:sel,tile:[tx,ty]});toast('已放置：'+(CNAME[sel]||sel));}draw();updateUI();saveLocal();}
var tapStart=null;
function onUp(ev){
  if(dragIdx>=0){dragIdx=-1;saveLocal();updateUI();}
  if(tapStart&&!tapStart.moved&&!tapStart.pan){doTap(tapStart.x,tapStart.y);}
  tapStart=null;pinch=null;}
'''
t = t[:i] + new + t[j:]
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("pan/zoom patched", len(t))
