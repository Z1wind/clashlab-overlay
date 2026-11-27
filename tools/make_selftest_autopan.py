# -*- coding: utf-8 -*-
"""自测：模拟拖拽到上边缘，验证自动平移让角点归一化 < -0.15。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
src = os.path.join(BASE, "android", "assets", "annotate7.html")
t = open(src, encoding="utf-8").read()
hook = '''
setTimeout(function(){
  try{
    document.getElementById('help').style.display='none';
    var s=S(); s.corners=[]; s.buildings=[];
    var cx=IMG.offX+IMG.w*0.3, cy=IMG.offY+IMG.h*0.3;
    doTap(cx,cy); doTap(cx+200,cy); doTap(cx+200,cy+200); doTap(cx,cy+200);
    var r=cv.getBoundingClientRect();
    function ev(x,y){return {preventDefault:function(){},touches:[{clientX:r.left+ (x*r.width/cv.width), clientY:r.top+(y*r.height/cv.height)}]};}
    var first=s.corners[0];
    onDown(ev(IMG.offX+IMG.w*0.3, IMG.offY+IMG.h*0.3));
    for(var i=0;i<60;i++){ onMove(ev(IMG.offX+IMG.w*0.3, 2)); }
    onUp(ev(IMG.offX+IMG.w*0.3, 2));
    var c=s.corners[0];
    document.getElementById('tip').textContent='SELFTEST2 before='+JSON.stringify(first)+' after='+JSON.stringify([+c[0].toFixed(3),+c[1].toFixed(3)])+' ok='+(c[1]<-0.15);
    draw();
  }catch(e){ document.getElementById('tip').textContent='SELFTEST2 ERR '+e; }
}, 2000);
'''
t = t.replace("</script></body></html>", hook + "\n</script></body></html>")
open(os.path.join(BASE, "android", "assets", "annotate7_selftest.html"), "w", encoding="utf-8", newline="\n").write(t)
print("selftest autopan written")
