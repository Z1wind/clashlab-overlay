# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "android", "assets", "annotate5.html")
t = open(p, encoding="utf-8").read()
old = """var palHidden=false;
document.getElementById('btnPalHide').onclick=function(){palHidden=!palHidden;var pal=document.getElementById('pal');
  pal.querySelector('#cattabs').style.display=palHidden?'none':'flex';
  pal.querySelector('#types').style.display=palHidden?'none':'flex';
  this.textContent=palHidden?'展开':'收';};
"""
if old in t:
    t = t.replace(old, "", 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("btnPalHide block removed")
else:
    print("block not found; searching")
    i = t.find("btnPalHide")
    print("idx:", i, t[i-80:i+160] if i>=0 else "")
