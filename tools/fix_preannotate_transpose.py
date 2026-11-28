# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "preannotate_core.py")
t = open(p, encoding="utf-8").read()
t = t.replace("        x = np.stack(crops)[:, :, :, ::-1].astype(np.float32) / 255.0",
              "        x = np.stack(crops)[:, :, :, ::-1].astype(np.float32) / 255.0\n        x = np.transpose(x, (0, 3, 1, 2))")
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("transpose fixed")
