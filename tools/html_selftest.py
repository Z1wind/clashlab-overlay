# -*- coding: utf-8 -*-
"""HTML 版自测：四角→放建筑→导出文档字段检查。"""
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
src = os.path.join(BASE, "dist", "ClashLabAnnotator_HTML_v1.0.html")
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
    var doc=saveDoc(s,IMGIDS[cur]);
    document.getElementById('tip').textContent='SELFTEST4 ver='+doc.version+' size='+doc.image_size+' image='+doc.image
      +' cn0='+JSON.stringify(doc.corners_norm[0])+' bld='+doc.buildings.length
      +' name='+((doc.buildings[0]||{}).name||'')+' tile='+JSON.stringify((doc.buildings[0]||{}).tile||[]);
  }catch(e){ document.getElementById('tip').textContent='SELFTEST4 ERR '+e; }
}, 2500);
'''
t = t.replace("</script></body></html>", hook + "\n</script></body></html>")
out = os.path.join(BASE, "dist", "annotator_selftest.html")
open(out, "w", encoding="utf-8", newline="\n").write(t)
print("selftest written", os.path.getsize(out))
