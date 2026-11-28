# -*- coding: utf-8 -*-
"""生成桌面版 HTML（pywebview 桥接保存 + 打开导出目录 + 快捷键）。"""
import base64, os, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
t = open(os.path.join(BASE, "dist", "ClashLabAnnotator_HTML_v1.1.html"), encoding="utf-8").read()
# 1) 桌面保存桥
bridge = '''
function hostSave(name,obj,done){
  if(window.pywebview&&window.pywebview.api&&window.pywebview.api.save_json){
    window.pywebview.api.save_json(name,JSON.stringify(obj)).then(function(r){
      if(r&&r.ok){toast('已保存：'+r.path);if(done)done();}
      else toast('保存失败：'+((r&&r.error)||'unknown'));
    });
    return true;
  }
  return false;
}
'''
t = t.replace("function exportOne(){", bridge + "function exportOne(){", 1)
# exportOne 优先走桌面保存
t = t.replace("var doc=saveDoc(s,IMGIDS[cur]);doc.saved_at=new Date().toISOString();var name='annot_b'+(cur+1<10?'0'+(cur+1):(cur+1))+'.json';",
              "var doc=saveDoc(s,IMGIDS[cur]);doc.saved_at=new Date().toISOString();var name='annot_b'+(cur+1<10?'0'+(cur+1):(cur+1))+'.json';if(hostSave(name,doc,autoNext))return;", 1)
t = t.replace("if(window.AndroidBridge&&window.AndroidBridge.saveFile){var r=window.AndroidBridge.saveFile('annot_all.json',JSON.stringify(all));",
              "if(hostSave('annot_all.json',all))return;if(window.AndroidBridge&&window.AndroidBridge.saveFile){var r=window.AndroidBridge.saveFile('annot_all.json',JSON.stringify(all));", 1)
# 2) 底部加「打开导出文件夹」
t = t.replace('<button id="btnExportAll"', '<button id="btnOpenDir" class="sec">导出文件夹</button><button id="btnExportAll"', 1)
anchor = "document.getElementById('btnExport').onclick=exportOne;"
add = ("var odEl=document.getElementById('btnOpenDir');if(odEl)odEl.onclick=function(){if(window.pywebview&&window.pywebview.api){window.pywebview.api.open_export_dir().then(function(r){if(r&&r.ok)toast('已打开：'+r.path);});}else toast('仅桌面版支持');};\n")
t = t.replace(anchor, add + anchor, 1)
# 3) 快捷键：Ctrl+Z 撤销 / Ctrl+S 导出 / 左右方向键切图
keys = '''
document.addEventListener('keydown',function(ev){
  if(ev.ctrlKey&&ev.key==='z'){ev.preventDefault();document.getElementById('btnUndo').click();}
  else if(ev.ctrlKey&&ev.key==='s'){ev.preventDefault();document.getElementById('btnExport').click();}
  else if(ev.key==='ArrowLeft'){document.getElementById('btnPrev').click();}
  else if(ev.key==='ArrowRight'){document.getElementById('btnNext').click();}
});
'''
t = t.replace("</script></body></html>", keys + "</script></body></html>")
t = re.sub(r"<title>.*?</title>", "<title>ClashLab 阵型标注（桌面版）</title>", t, count=1)
t = t.replace("<h3>30 秒上手（HTML v1.1）</h3>", "<h3>30 秒上手（桌面版）</h3>")
out = os.path.join(BASE, "dist", "ClashLabAnnotator_HTML_desktop.html")
open(out, "w", encoding="utf-8", newline="\n").write(t)
print("desktop html", os.path.getsize(out))
