# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "eval_centernet_fast.py")
t = open(p, encoding="utf-8").read()
t = t.replace('    if w < 8 or h < 8: continue', '    w = max(w, 48.0); h = max(h, 48.0)  # 尺寸头未收敛时给兜底框')
t = t.replace('peaks = (hmax == hm) & (hm > 0.30)', 'peaks = (hmax == hm) & (hm > 0.60)')
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("eval patched")
