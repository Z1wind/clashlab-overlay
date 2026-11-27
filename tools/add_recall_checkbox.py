# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "annotator.py")
t = open(p, encoding="utf-8").read()
if 'id="candrecall"' not in t:
    t = t.replace('<span id="candthrv" style="font-size:11px;color:#8fa3bd">0.85</span>',
                  '<span id="candthrv" style="font-size:11px;color:#8fa3bd">0.85</span>\n  <label style="font-size:11px;color:#9fb3c8"><input type="checkbox" id="candrecall"> 召回优先</label>')
    t = t.replace('gate_threshold:parseFloat(document.getElementById("candthr").value)})',
                  'gate_threshold:parseFloat(document.getElementById("candthr").value),\n          recall:document.getElementById("candrecall").checked})')
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("recall checkbox added")
