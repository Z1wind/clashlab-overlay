# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "desktop_app.py")
t = open(p, encoding="utf-8").read()
old = '''            th = {"standard": (0.85, 0.85), "recall": (0.70, 0.70), "precise": (0.92, 0.92)}.get(mode, (0.85, 0.85))
            out = get_annotator().detect(img, quad, gate_th=th[0], emb_th=th[1])'''
new = '''            cfg = {
                "standard": (0.85, 0.85, (0.0,)),
                "recall": (0.70, 0.70, (0.0,)),
                "precise": (0.90, 0.85, (0.0, 0.5)),  # 少错：半格合并，精度 +7pt（CV）
            }.get(mode, (0.85, 0.85, (0.0,)))
            out = get_annotator().detect(img, quad, gate_th=cfg[0], emb_th=cfg[1], phases=cfg[2])'''
if old in t:
    t = t.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("precise mode -> half-phase")
else:
    print("anchor miss")
