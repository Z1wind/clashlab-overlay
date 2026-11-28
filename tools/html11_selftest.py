# -*- coding: utf-8 -*-
"""HTML v1.1 自测：四角→网格像素→滚轮缩放→左键拖动平移。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
src = os.path.join(BASE, "dist", "ClashLabAnnotator_HTML_v1.1.html")
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
    draw();
    var d=ctx.getImageData(0,0,cv.width,cv.height).data,grid=0;
    for(var i=0;i<d.length;i+=4){ if(d[i]<100&&d[i+1]>180&&d[i+2]>180) grid++; }
    var r=cv.getBoundingClientRect();
    try{ cv.dispatchEvent(new WheelEvent('wheel',{clientX:r.left+300,clientY:r.top+200,deltaY:-120,bubbles:true,cancelable:true})); }catch(e){}
    var sc=view.scale, pan0=view.panX;
    try{
      cv.dispatchEvent(new MouseEvent('mousedown',{clientX:r.left+400,clientY:r.top+300,bubbles:true,cancelable:true}));
      cv.dispatchEvent(new MouseEvent('mousemove',{clientX:r.left+480,clientY:r.top+340,bubbles:true,cancelable:true}));
      window.dispatchEvent(new MouseEvent('mouseup',{clientX:r.left+480,clientY:r.top+340,bubbles:true,cancelable:true}));
    }catch(e){}
    document.getElementById('tip').textContent='SELFTEST6 grid='+grid+' scale='+sc.toFixed(2)+' panMoved='+(Math.abs(view.panX-pan0)>1)+' panX='+view.panX.toFixed(1)+' corners='+S().corners.length;
  }catch(e){ document.getElementById('tip').textContent='SELFTEST6 ERR '+e; }
}, 2500);
'''
t = t.replace("</script></body></html>", hook + "\n</script></body></html>")
open(os.path.join(BASE, "dist", "html11_selftest.html"), "w", encoding="utf-8", newline="\n").write(t)
print("selftest written")
