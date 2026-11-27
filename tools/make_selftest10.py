# -*- coding: utf-8 -*-
"""自测 v0.3.0：放建筑 → 模拟拖动 → tile 变化。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
src = os.path.join(BASE, "android", "assets", "annotate10.html")
t = open(src, encoding="utf-8").read()
hook = '''
setTimeout(function(){
  try{
    document.getElementById('help').style.display='none';
    var s=S(); s.corners=[]; s.buildings=[];
    doTap(IMG.offX+IMG.w*0.25, IMG.offY+IMG.h*0.25);
    doTap(IMG.offX+IMG.w*0.85, IMG.offY+IMG.h*0.25);
    doTap(IMG.offX+IMG.w*0.85, IMG.offY+IMG.h*0.85);
    doTap(IMG.offX+IMG.w*0.25, IMG.offY+IMG.h*0.85);
    var cx=IMG.offX+IMG.w*0.5, cy=IMG.offY+IMG.h*0.5;
    doTap(cx,cy);
    var before=JSON.stringify(s.buildings[0].tile);
    var r=cv.getBoundingClientRect();
    function ev(x,y){return {preventDefault:function(){},touches:[{clientX:r.left+x*r.width/cv.width, clientY:r.top+y*r.height/cv.height}]};}
    onDown(ev(cx,cy));
    onMove(ev(cx+40,cy));
    onMove(ev(cx+80,cy+30));
    onUp(ev(cx+80,cy+30));
    var after=JSON.stringify(s.buildings[0].tile);
    document.getElementById('tip').textContent='SELFTEST3 before='+before+' after='+after+' changed='+(before!==after)+' n='+s.buildings.length;
  }catch(e){ document.getElementById('tip').textContent='SELFTEST3 ERR '+e; }
}, 2000);
'''
t = t.replace("</script></body></html>", hook + "\n</script></body></html>")
open(os.path.join(BASE, "android", "assets", "annotate10_selftest.html"), "w", encoding="utf-8", newline="\n").write(t)
print("selftest3 written")
