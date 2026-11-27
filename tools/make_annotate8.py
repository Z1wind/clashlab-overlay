# -*- coding: utf-8 -*-
"""v0.2.8：导出成功后自动跳到下一张未标定的图（修正版：加花括号）。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
src = os.path.join(BASE, "android", "assets", "annotate7.html")
dst = os.path.join(BASE, "android", "assets", "annotate8.html")
t = open(src, encoding="utf-8").read()
t = t.replace("<h3>30 秒上手（v0.2.7）</h3>", "<h3>30 秒上手（v0.2.8）</h3>")
old = ("if(window.AndroidBridge&&window.AndroidBridge.saveFile){var r=window.AndroidBridge.saveFile(name,JSON.stringify(doc));"
       "if(r&&r.indexOf('OK:')===0)toast('已保存到下载：'+name);else if(r&&r.indexOf('OK')===0)toast('已保存到 App 目录：'+name);"
       "else toast('保存失败：'+r);}")
new = ("if(window.AndroidBridge&&window.AndroidBridge.saveFile){var r=window.AndroidBridge.saveFile(name,JSON.stringify(doc));"
       "if(r&&r.indexOf('OK:')===0){toast('已保存到下载：'+name);autoNext();}"
       "else if(r&&r.indexOf('OK')===0){toast('已保存到 App 目录：'+name);autoNext();}"
       "else toast('保存失败：'+r);}")
if old in t:
    t = t.replace(old, new, 1)
    print("export hook braced")
else:
    print("export anchor miss")
anchor = "function exportAll(){"
add = '''function autoNext(){for(var j=cur+1;j<IMAGES.length;j++){var s=state[j];
  if(!s||!s.corners||s.corners.length<4){(function(jj){setTimeout(function(){loadImage(jj);toast('已跳到第 '+(jj+1)+' 张');},350);})(j);return;}}}
'''
t = t.replace(anchor, add + anchor, 1)
open(dst, "w", encoding="utf-8", newline="\n").write(t)
print("annotate8 written", len(t))
