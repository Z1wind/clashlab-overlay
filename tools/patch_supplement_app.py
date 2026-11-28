# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
# 1) desktop_app: preannotate 支持 existing 与 append 标记
p = os.path.join(BASE, "tools", "desktop_app.py")
t = open(p, encoding="utf-8").read()
old_sig = "    def preannotate(self, corners_norm, image_size, image_rel, mode=\"standard\"):"
new_sig = "    def preannotate(self, corners_norm, image_size, image_rel, mode=\"standard\", existing=None):"
t = t.replace(old_sig, new_sig, 1)
old_detect = "            out = get_annotator().detect(img, quad, gate_th=cfg[0], emb_th=cfg[1], phases=cfg[2])"
new_detect = ("            out = get_annotator().detect(img, quad, gate_th=cfg[0], emb_th=cfg[1], phases=cfg[2])\n"
              "            if existing:\n"
              "                ex = [(float(a), float(b)) for a, b in existing]\n"
              "                out = [o for o in out if all(abs(o[\"center\"][0]-a) + abs(o[\"center\"][1]-b) > 1.2 for a, b in ex)]")
if old_detect in t:
    t = t.replace(old_detect, new_detect, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("app: existing filter added")
else:
    print("app anchor miss")
