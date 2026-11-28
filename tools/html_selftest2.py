# -*- coding: utf-8 -*-
"""HTML 版自测 2：导出分支捕获 + IMGIDS 精确值。"""
import os
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
    var cap={};var origCreate=document.createElement.bind(document);
    document.createElement=function(tag){var el=origCreate(tag);if(tag==='a'){el.click=function(){cap.dl=el.download;cap.prefix=String(el.href).slice(0,26);cap.len=String(el.href).length;};}return el;};
    exportOne();
    document.createElement=origCreate;
    var a=cap;
    document.getElementById('tip').textContent='SELFTEST5 imgid='+IMGIDS[0]+' dl='+a.dl+' prefix='+a.prefix+' len='+a.len+' toast='+document.getElementById('toast').textContent;
  }catch(e){ document.getElementById('tip').textContent='SELFTEST5 ERR '+e; }
}, 2500);
'''
t = t.replace("</script></body></html>", hook + "\n</script></body></html>")
open(os.path.join(BASE, "dist", "annotator_selftest5.html"), "w", encoding="utf-8", newline="\n").write(t)
print("selftest5 written")
