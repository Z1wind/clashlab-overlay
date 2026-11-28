# -*- coding: utf-8 -*-
"""桌面 HTML v5：增加「补充预标注」按钮（保留已放建筑）。"""
import os, re
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
src = os.path.join(BASE, "dist", "ClashLabAnnotator_Desktop_v4.html")
t = open(src, encoding="utf-8").read()
t = re.sub(r"<title>.*?</title>", "<title>ClashLab 阵型标注（桌面版 v2.0）</title>", t, count=1)
t = t.replace("<h3>30 秒上手（桌面版 v1.6）</h3>", "<h3>30 秒上手（桌面版 v2.0）</h3>")
t = t.replace('<button id="btnPre" class="sec">自动预标注</button>',
              '<button id="btnPre" class="sec">自动预标注</button><button id="btnPreAdd" class="sec">补充预标注</button>', 1)
js = r'''
(function(){
  function ready(fn){ var n=0; (function tick(){ n++; if(window.pywebview&&pywebview.api&&document.getElementById('btnPreAdd')){ try{fn();}catch(e){} } else if(n<300){ setTimeout(tick,80); } })(); }
  ready(function(){
    var btn = document.getElementById('btnPreAdd');
    btn.onclick = function(){
      var s=S(); if(s.corners.length<4){toast('先点四个角');return;}
      if(!window.pywebview||!pywebview.api||!pywebview.api.preannotate){toast('当前环境不支持模型推理');return;}
      var i = parseInt(localStorage.getItem('clashlab_pre_mode')||'0',10)||0;
      var MODES=[["standard","标准"],["recall","多标"],["precise","少错"]];
      var mode = MODES[i][0];
      var existing = s.buildings.map(function(b){return [b.tile[0]+1, b.tile[1]+1];});
      var cn = s.corners.map(function(p){return [p[0],p[1]];});
      this.disabled = true; this.textContent = '补充中…';
      pywebview.api.preannotate(cn,[img.naturalWidth,img.naturalHeight],IMGIDS[cur],mode,existing).then(function(r){
        btn.disabled=false; btn.textContent='补充预标注';
        if(!r||!r.ok){toast('预标注失败：'+((r&&r.error)||'unknown'));return;}
        var preds=r.buildings||[];
        if(!preds.length){toast('没有可补充的建筑');return;}
        preds.forEach(function(b){ s.buildings.push({type:b.type,tile:b.tile}); });
        draw(); updateUI(); saveLocal(); document.getElementById('tip').textContent=tipText();
        toast('补充了 '+preds.length+' 栋（'+MODES[i][1]+'）');
      }).catch(function(e){ btn.disabled=false; btn.textContent='补充预标注'; toast('识别异常：'+e); });
    };
  });
})();
'''
t = t.replace("</script></body></html>", js + "\n</script></body></html>")
out = os.path.join(BASE, "dist", "ClashLabAnnotator_Desktop_v5.html")
open(out, "w", encoding="utf-8", newline="\n").write(t)
print("desktop v5 html", os.path.getsize(out))
