# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "grid_from_walls.py")
t = open(p, encoding="utf-8").read()
t = t.replace('keep = (xs > img.shape[1] * 0.04) & (xs < img.shape[1] * 0.96) & (ys > img.shape[0] * 0.04) & (ys < img.shape[0] * 0.96)',
              'keep = (xs > img.shape[1] * 0.12) & (xs < img.shape[1] * 0.90) & (ys > img.shape[0] * 0.05) & (ys < img.shape[0] * 0.80)')
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("patched margins")
