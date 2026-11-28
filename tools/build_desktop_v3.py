# -*- coding: utf-8 -*-
"""桌面 v3：加「自动预标注」按钮（调用 pywebview.api.preannotate）。"""
import os, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
src = os.path.join(BASE, "dist", "ClashLabAnnotator_Desktop_v2.html")
t = open(src, encoding="utf-8").read()
t = re.sub(r"<title>.*?</title>", "<title>ClashLab 阵型标注（桌面版 v1.3）</title>", t, count=1)
t = t.replace("<h3>30 秒上手（桌面版 v1.2）</h3>", "<h3>30 秒上手（桌面版 v1.3）</h3>")
t = t.replace("点四角：<b>左键单击</b>；按住黄点拖动可微调（可拖出图片）。<b>滚轮缩放、左键拖动平移</b>。",
              "点四角后点「自动预标注」，模型会先自动放一批建筑，你再删误报/补漏。<b>滚轮缩放、左键拖动平移</b>。")
# 顶部栏加按钮
t = t.replace('<button id="btnNext">下一张</button>', '<button id="btnPre" class="sec">自动预标注</button><button id="btnNext">下一张</button>', 1)
js = r'''
(function(){
  function ready(fn){ var n=0; (function tick(){ n++; if(window.pywebview&&pywebview.api&&document.getElementById('btnPre')){ try{fn();}catch(e){} } else if(n<300){ setTimeout(tick, 80); } })(); }
  ready(function(){
    document.getElementById('btnPre').onclick=function(){
      var s=S(); if(s.corners.length<4){toast('先点四个角');return;}
      if(!window.pywebview||!pywebview.api||!pywebview.api.preannotate){toast('当前环境不支持模型推理');return;}
      var btn=this; btn.disabled=true; btn.textContent='识别中…';
      var cn=s.corners.map(function(p){return [p[0],p[1]];});
      pywebview.api.preannotate(cn,[img.naturalWidth,img.naturalHeight],IMGIDS[cur]).then(function(r){
        btn.disabled=false; btn.textContent='自动预标注';
        if(!r||!r.ok){toast('预标注失败：'+((r&&r.error)||'unknown'));return;}
        var preds=r.buildings||[];
        if(!preds.length){toast('没识别到建筑');return;}
        var msg='识别到 '+preds.length+' 栋（用时 '+r.ms+'ms），替换当前已放建筑？';
        if(s.buildings.length && !confirm(msg)) return;
        s.buildings=preds.map(function(b){return {type:b.type,tile:b.tile};});
        draw(); updateUI(); saveLocal(); document.getElementById('tip').textContent=tipText();
        toast('已预标注 '+preds.length+' 栋，请检查并删除误报');
      }).catch(function(e){ btn.disabled=false; btn.textContent='自动预标注'; toast('识别异常：'+e); });
    };
  });
})();
'''
t = t.replace("</script></body></html>", js + "\n</script></body></html>")
out = os.path.join(BASE, "dist", "ClashLabAnnotator_Desktop_v3.html")
open(out, "w", encoding="utf-8", newline="\n").write(t)
print("desktop v3 html", os.path.getsize(out))
