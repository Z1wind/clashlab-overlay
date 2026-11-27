# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "android", "assets", "annotate6.html")
t = open(p, encoding="utf-8").read()
t = t.replace("<h3>30 秒上手（v0.2.3）</h3>", "<h3>30 秒上手（v0.2.5）</h3>")
t = t.replace("黄点出现后<b>按住可拖动</b>到真正的角。图片太小？右下角 <b>＋ / － / 适应</b> 可缩放；两根手指捏合也能缩放。",
              "黄点出现后<b>按住可拖动</b>到真正的角。图片太小：<b>双击图面 2x 放大</b>，或用右上 <b>＋ / － / 适应</b>，也可双指捏合。")
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("help updated")
