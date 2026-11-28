# -*- coding: utf-8 -*-
"""桌面 v2 自测 v2：右键删除用建筑自身位置。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
src = os.path.join(BASE, "dist", "ClashLabAnnotator_Desktop_v2.html")
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
    doTap(IMG.offX+IMG.w*0.5, IMG.offY+IMG.h*0.5);
    var placed=s.buildings.length;
    var b=s.buildings[0]; var cp=bil((b.tile[0]+.5)/44,(b.tile[1]+.5)/44);
    var r=cv.getBoundingClientRect();
    function mev(type,x,y){ return new MouseEvent(type,{clientX:r.left+x*r.width/cv.width,clientY:r.top+y*r.height/cv.height,bubbles:true,cancelable:true}); }
    cv.dispatchEvent(mev('mousemove',cp[0],cp[1]));
    var coord=document.getElementById('coord')?document.getElementById('coord').textContent:'';
    cv.dispatchEvent(mev('contextmenu',cp[0],cp[1]));
    var afterDel=s.buildings.length;
    var redoBtn=!!document.getElementById('btnRedo');
    var errShown=(document.getElementById('tip').textContent||'').indexOf('ERR')>=0;
    document.getElementById('tip').textContent='DSKTEST2 placed='+placed+' tile='+JSON.stringify(b.tile)+' afterRightClick='+afterDel+' coord="'+coord+'" redoBtn='+redoBtn+' err='+errShown;
  }catch(e){ document.getElementById('tip').textContent='DSKTEST2 ERR '+e; }
}, 3000);
'''
t = t.replace("</script></body></html>", hook + "\n</script></body></html>")
open(os.path.join(BASE, "dist", "desktop_v2_selftest2.html"), "w", encoding="utf-8", newline="\n").write(t)
print("selftest2 written")
