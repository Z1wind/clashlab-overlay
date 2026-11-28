# -*- coding: utf-8 -*-
"""桌面 HTML v4：预标注模式切换（标准/多标/少错）。"""
import os, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
src = os.path.join(BASE, "dist", "ClashLabAnnotator_Desktop_v3.html")
t = open(src, encoding="utf-8").read()
t = re.sub(r"<title>.*?</title>", "<title>ClashLab 阵型标注（桌面版 v1.6）</title>", t, count=1)
t = t.replace("<h3>30 秒上手（桌面版 v1.3）</h3>", "<h3>30 秒上手（桌面版 v1.6）</h3>")
t = t.replace('<button id="btnPre" class="sec">自动预标注</button>',
              '<button id="btnMode" class="sec">模式：标准</button><button id="btnPre" class="sec">自动预标注</button>', 1)
js = r'''
(function(){
  var MODES = [["standard","标准"],["recall","多标"],["precise","少错"]];
  function apply(){
    var i = parseInt(localStorage.getItem('clashlab_pre_mode')||'0',10)||0;
    var btn = document.getElementById('btnMode');
    if(btn) btn.textContent = '模式：' + MODES[i][1];
  }
  function ready(fn){ var n=0; (function tick(){ n++; if(window.pywebview&&pywebview.api&&document.getElementById('btnMode')){ try{fn();}catch(e){} } else if(n<300){ setTimeout(tick, 80); } })(); }
  ready(function(){
    apply();
    document.getElementById('btnMode').onclick = function(){
      var i = (parseInt(localStorage.getItem('clashlab_pre_mode')||'0',10)||0);
      i = (i+1) % MODES.length;
      localStorage.setItem('clashlab_pre_mode', String(i));
      apply();
      toast('预标注模式：' + MODES[i][1]);
    };
    // 预标注调用带上模式
    var oldClick = document.getElementById('btnPre').onclick;
    document.getElementById('btnPre').onclick = function(){
      var i = (parseInt(localStorage.getItem('clashlab_pre_mode')||'0',10)||0);
      var mode = MODES[i][0];
      var s=S(); if(s.corners.length<4){toast('先点四个角');return;}
      if(!window.pywebview||!pywebview.api||!pywebview.api.preannotate){toast('当前环境不支持模型推理');return;}
      var btn=this; btn.disabled=true; btn.textContent='识别中…';
      var cn=s.corners.map(function(p){return [p[0],p[1]];});
      pywebview.api.preannotate(cn,[img.naturalWidth,img.naturalHeight],IMGIDS[cur],mode).then(function(r){
        btn.disabled=false; btn.textContent='自动预标注';
        if(!r||!r.ok){toast('预标注失败：'+((r&&r.error)||'unknown'));return;}
        var preds=r.buildings||[];
        if(!preds.length){toast('没识别到建筑（可试试「多标」模式）');return;}
        var msg='识别到 '+preds.length+' 栋（'+r.ms+'ms），替换当前已放建筑？';
        if(s.buildings.length && !confirm(msg)) return;
        s.buildings=preds.map(function(b){return {type:b.type,tile:b.tile};});
        draw(); updateUI(); saveLocal(); document.getElementById('tip').textContent=tipText();
        toast('已预标注 '+preds.length+' 栋（'+MODES[i][1]+'），请检查');
      }).catch(function(e){ btn.disabled=false; btn.textContent='自动预标注'; toast('识别异常：'+e); });
    };
  });
})();
'''
t = t.replace("</script></body></html>", js + "\n</script></body></html>")
out = os.path.join(BASE, "dist", "ClashLabAnnotator_Desktop_v4.html")
open(out, "w", encoding="utf-8", newline="\n").write(t)
print("desktop v4 html", os.path.getsize(out))
