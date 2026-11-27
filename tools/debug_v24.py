# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "android", "assets", "annotate5.html")
t = open(p, encoding="utf-8").read()
if "window.onerror" not in t:
    t = t.replace("<script>\n", "<script>\nwindow.onerror=function(m,s,l,c,e){try{document.getElementById('tip').textContent='ERR: '+m+' @'+l;}catch(x){}};\n", 1)
    t = t.replace("function loadImage(idx){", "function loadImage(idx){try{", 1)
    t = t.replace("img.src=IMAGES[idx];updateUI();}", "img.src=IMAGES[idx];updateUI();}catch(e){document.getElementById('tip').textContent='LOADERR: '+e;}}", 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("debug hooks added")
