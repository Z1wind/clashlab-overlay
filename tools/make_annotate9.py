# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
src = os.path.join(BASE, "android", "assets", "annotate8.html")
dst = os.path.join(BASE, "android", "assets", "annotate9.html")
t = open(src, encoding="utf-8").read()
t = t.replace("<h3>30 秒上手（v0.2.8）</h3>", "<h3>30 秒上手（v0.2.9）</h3>")
old = "function loadImage(idx){try{cur=idx;document.getElementById('tip').textContent='第 '+(idx+1)+'/'+IMAGES.length+' 张';"
new = ("function doneCount(){var n=0;for(var i=0;i<IMAGES.length;i++){var s=state[i];if(s&&s.corners&&s.corners.length===4)n++;}return n;}\n"
       "function tipText(){return '第 '+(cur+1)+'/'+IMAGES.length+' 张 · 已完成 '+doneCount();}\n"
       "function loadImage(idx){try{cur=idx;document.getElementById('tip').textContent=tipText();")
t = t.replace(old, new, 1)
t = t.replace("function updateUI(){var s=S();", "function updateUI(){var s=S();try{document.getElementById('tip').textContent=tipText();}catch(e){}", 1)
open(dst, "w", encoding="utf-8", newline="\n").write(t)
ok1 = "function doneCount" in t and "function tipText" in t
print("annotate9 written", len(t), "| hooks:", ok1)
