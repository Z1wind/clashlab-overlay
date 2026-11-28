# -*- coding: utf-8 -*-
"""桌面 v2 真实鼠标事件自测：点击放四角/放建筑，拖动平移。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
src = os.path.join(BASE, "dist", "ClashLabAnnotator_Desktop_v2.html")
t = open(src, encoding="utf-8").read()
hook = '''
setTimeout(function(){
  try{
    document.getElementById('help').style.display='none';
    var s=S(); s.corners=[]; s.buildings=[]; draw(); updateUI();
    var r=cv.getBoundingClientRect();
    function cev(type,x,y,target){ var el=target||cv; return new MouseEvent(type,{clientX:r.left+x*r.width/cv.width, clientY:r.top+y*r.height/cv.height, bubbles:true, cancelable:true, button:0}); }
    function click(x,y){ cv.dispatchEvent(cev('mousedown',x,y)); window.dispatchEvent(cev('mouseup',x,y,window)); }
    click(IMG.offX+IMG.w*0.25, IMG.offY+IMG.h*0.25);
    click(IMG.offX+IMG.w*0.85, IMG.offY+IMG.h*0.25);
    click(IMG.offX+IMG.w*0.85, IMG.offY+IMG.h*0.85);
    click(IMG.offX+IMG.w*0.25, IMG.offY+IMG.h*0.85);
    var nCorners=S().corners.length;
    click(IMG.offX+IMG.w*0.5, IMG.offY+IMG.h*0.5);
    var nBld=S().buildings.length;
    draw();
    var d=ctx.getImageData(0,0,cv.width,cv.height).data,grid=0;
    for(var i=0;i<d.length;i+=4){ if(d[i]<100&&d[i+1]>180&&d[i+2]>180) grid++; }
    // 左键拖动平移
    var cx=IMG.offX+IMG.w*0.6, cy=IMG.offY+IMG.h*0.6;
    cv.dispatchEvent(cev('mousedown',cx,cy));
    cv.dispatchEvent(cev('mousemove',cx+60,cy+30));
    cv.dispatchEvent(cev('mousemove',cx+120,cy+60));
    window.dispatchEvent(cev('mouseup',cx+120,cy+60,window));
    var panned=(Math.abs(view.panX)>1||Math.abs(view.panY)>1);
    document.getElementById('tip').textContent='CLICKTEST corners='+nCorners+' bld='+nBld+' grid='+grid+' panned='+panned+' pan=('+view.panX.toFixed(0)+','+view.panY.toFixed(0)+')';
  }catch(e){ document.getElementById('tip').textContent='CLICKTEST ERR '+e; }
}, 3000);
'''
t = t.replace("</script></body></html>", hook + "\n</script></body></html>")
open(os.path.join(BASE, "dist", "click_selftest.html"), "w", encoding="utf-8", newline="\n").write(t)
print("click selftest written")
