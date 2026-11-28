# -*- coding: utf-8 -*-
"""桌面交互版 HTML v2：右键删除、悬停高亮、光标、坐标/缩放、撤销重做、快捷键。"""
import os, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
src = os.path.join(BASE, "dist", "ClashLabAnnotator_HTML_desktop.html")
t = open(src, encoding="utf-8").read()

# 1) 还原桌面版基础上再加桌面交互（标题/帮助）
t = re.sub(r"<title>.*?</title>", "<title>ClashLab 阵型标注（桌面版 v1.1）</title>", t, count=1)
t = t.replace("<h3>30 秒上手（桌面版）</h3>", "<h3>30 秒上手（桌面版 v1.1）</h3>")
t = t.replace("黄点出现后<b>按住可拖动</b>到真正的角，可拖到图片外面。<b>滚轮缩放、左键拖动平移画面</b>。",
              "点四角：<b>左键单击</b>；按住黄点拖动可微调（可拖出图片）。<b>滚轮缩放、左键拖动平移</b>。")
t = t.replace("图片太小：<b>滚轮缩放</b>，或右上 <b>＋ / － / 适应</b>；<b>左键拖动</b>可平移画面。",
              "放大：滚轮或右上 ＋/－/适应。右键/Building 上：<b>右键删除</b>；Delete 删除悬停建筑；Esc 收起类型面板；Ctrl+Z 撤销、Ctrl+Y 重做。")
t = t.replace("「导出全部」保存 JSON 到浏览器下载目录；进度自动存在本机浏览器。",
              "「导出全部」直接保存到 Downloads\\ClashLab标注；进度自动保存。")

# 2) 底部加「重做」按钮
t = t.replace('<button id="btnUndo">撤销</button>', '<button id="btnUndo">撤销</button><button id="btnRedo">重做</button>', 1)

# 3) 注入桌面交互脚本
desktop_js = r'''
(function(){
  function whenReady(fn){ var n=0; (function tick(){ n++; if(document.getElementById('cv')&&window.IMGIDS&&IMGIDS.length){ try{fn();}catch(e){document.getElementById('tip').textContent='DESKTOP ERR '+e;} } else if(n<200){ setTimeout(tick,50); } })(); }
  whenReady(function(){
    var coordEl=document.getElementById('coord');
    if(!coordEl){ coordEl=document.createElement('div'); coordEl.id='coord';
      coordEl.style.cssText='position:absolute;left:8px;bottom:64px;z-index:8;background:rgba(17,23,32,.85);color:#9fd6ef;font:12px monospace;padding:3px 7px;border-radius:4px;pointer-events:none';
      document.getElementById('stage').appendChild(coordEl); }
    var hoverBld=-1, hoverCorner=-1, undoStack=[], redoStack=[], applying=false;
    var _save=window.saveLocal;
    window.saveLocal=function(){ if(!applying){ try{ undoStack.push(JSON.stringify(state)); if(undoStack.length>80)undoStack.shift(); redoStack.length=0; }catch(e){} } return _save(); };
    function applySnap(snap){ applying=true; try{ state=JSON.parse(snap); }catch(e){} var savedCur=cur; applying=false; loadImage(savedCur); draw(); updateUI(); }
    function doUndo(){ if(!undoStack.length){toast('没有可撤销的');return;} try{redoStack.push(JSON.stringify(state));}catch(e){} applySnap(undoStack.pop()); toast('已撤销'); }
    function doRedo(){ if(!redoStack.length){toast('没有可重做');return;} try{undoStack.push(JSON.stringify(state));}catch(e){} applySnap(redoStack.pop()); toast('已重做'); }
    document.getElementById('btnUndo').onclick=doUndo;
    var rb=document.getElementById('btnRedo'); if(rb) rb.onclick=doRedo;
    // 悬停环
    var _draw=window.draw; window.draw=function(){ _draw(); try{ if(hoverBld>=0){ var bb=S().buildings[hoverBld]; if(bb){ var cp=bil((bb.tile[0]+.5)/44,(bb.tile[1]+.5)/44); var x=view.panX+cp[0]*view.scale, y=view.panY+cp[1]*view.scale; ctx.save(); ctx.beginPath(); ctx.arc(x,y,15,0,7); ctx.strokeStyle='#ff5a5a'; ctx.lineWidth=2.5; ctx.stroke(); ctx.restore(); } } }catch(e){} };
    function updCoord(ev){ var s=S(); var txt=''; if(s.corners.length===4){ var p=screenToCanvas(ev); var uv=invBilinear(p[0],p[1]); txt='格 '+Math.floor(uv[0]*44)+','+Math.floor(uv[1]*44); } else { txt='点四角（已点 '+s.corners.length+'/4）'; } coordEl.textContent=txt+' | 缩放 '+Math.round(view.scale*100)+'%'; }
    cv.addEventListener('mousemove',function(ev){
      var s=S(); var p=screenToCanvas(ev); hoverBld=-1; hoverCorner=-1;
      if(s.corners.length===4){ hoverBld=nearestBuilding(p[0],p[1]); }
      else if(s.corners.length){ hoverCorner=nearestCorner(p[0],p[1]); }
      cv.style.cursor = hoverCorner>=0 ? 'grab' : (hoverBld>=0 ? 'pointer' : (ev.buttons ? 'grabbing' : 'crosshair'));
      updCoord(ev);
    });
    cv.addEventListener('mousedown',function(){ cv.style.cursor='grabbing'; });
    window.addEventListener('mouseup',function(){ cv.style.cursor='crosshair'; });
    cv.addEventListener('contextmenu',function(ev){ ev.preventDefault(); var s=S(); if(s.corners.length!==4)return; var p=screenToCanvas(ev); var bi=nearestBuilding(p[0],p[1]); if(bi>=0){ s.buildings.splice(bi,1); hoverBld=-1; draw(); updateUI(); saveLocal(); toast('已删除（右键）'); } });
    cv.addEventListener('dragstart',function(ev){ ev.preventDefault(); });
    document.addEventListener('keydown',function(ev){
      var tag=(ev.target&&ev.target.tagName)||''; if(tag==='INPUT'||tag==='TEXTAREA')return;
      if(ev.key==='Escape'){ try{palOpen(false);}catch(e){} hoverBld=-1; draw(); return; }
      if(ev.key==='Delete'||ev.key==='Backspace'){ var s=S(); if(hoverBld>=0&&s.buildings[hoverBld]){ s.buildings.splice(hoverBld,1); hoverBld=-1; draw(); updateUI(); saveLocal(); toast('已删除'); ev.preventDefault(); } return; }
      if(ev.ctrlKey&&(ev.key==='y'||ev.key==='Y')){ ev.preventDefault(); doRedo(); return; }
      if(ev.ctrlKey&&(ev.key==='z'||ev.key==='Z')){ ev.preventDefault(); doUndo(); return; }
      if(ev.key==='+'||ev.key==='='){ document.getElementById('btnZoomIn').click(); }
      else if(ev.key==='-'){ document.getElementById('btnZoomOut').click(); }
      else if(ev.key==='0'){ document.getElementById('btnZoomFit').click(); }
    });
    cv.style.cursor='crosshair';
    if(typeof updCoord==='function'){ /* noop */ }
  });
})();
'''
t = t.replace("</script></body></html>", desktop_js + "\n</script></body></html>")
out = os.path.join(BASE, "dist", "ClashLabAnnotator_Desktop_v2.html")
open(out, "w", encoding="utf-8", newline="\n").write(t)
print("wrote", out, os.path.getsize(out))
