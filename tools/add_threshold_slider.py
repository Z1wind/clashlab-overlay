# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat".replace("\\\\", "\\")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "annotator.py")
t = open(p, encoding="utf-8").read()
if 'id="candthr"' not in t:
    t = t.replace('<button id="candbtn" title="门控模型给建筑位置，类型用当前选中">位置候选</button>',
                  '<button id="candbtn" title="门控模型给建筑位置，类型用当前选中">位置候选</button>\n  <input id="candthr" type="range" min="0.50" max="0.98" step="0.01" value="0.85" style="width:90px" title="门控阈值：越低候选越多、误报越多">\n  <span id="candthrv" style="font-size:11px;color:#8fa3bd">0.85</span>')
    t = t.replace('body:JSON.stringify({quad:corners,max_n:40,gate_only:true})',
                  'body:JSON.stringify({quad:corners,max_n:60,gate_only:true,gate_threshold:parseFloat(document.getElementById("candthr").value)})')
    t = t.replace("cands=j.items||[]; candsActive=true; st();",
                  "cands=j.items||[]; candsActive=true; st(); document.getElementById('candthrv').textContent=parseFloat(document.getElementById('candthr').value).toFixed(2);")
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("threshold slider added")
