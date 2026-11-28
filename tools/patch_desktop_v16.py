# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "desktop_app.py")
t = open(p, encoding="utf-8").read()
t = t.replace('APP_TITLE = "ClashLab 阵型标注（桌面版 v1.5）"', 'APP_TITLE = "ClashLab 阵型标注（桌面版 v1.6）"')
t = t.replace('html = resource_path("ClashLabAnnotator_Desktop_v3.html")', 'html = resource_path("ClashLabAnnotator_Desktop_v4.html")')
old = "    def preannotate(self, corners_norm, image_size, image_rel):"
new = "    def preannotate(self, corners_norm, image_size, image_rel, mode=\"standard\"):"
t = t.replace(old, new, 1)
old2 = "            out = get_annotator().detect(img, quad)"
new2 = ("            th = {\"standard\": (0.85, 0.85), \"recall\": (0.70, 0.70), \"precise\": (0.92, 0.92)}.get(mode, (0.85, 0.85))\n"
        "            out = get_annotator().detect(img, quad, gate_th=th[0], emb_th=th[1])")
t = t.replace(old2, new2, 1)
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("desktop_app v1.6 patched (mode thresholds)")
