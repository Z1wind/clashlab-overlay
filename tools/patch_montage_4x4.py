# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "war_base_montage.py")
t = open(p, encoding="utf-8").read()
t = t.replace('''            it = items[i]; x, y = it["tile"]; size = it["size"]
            m = 1
            x0 = max(0, x - m); y0 = max(0, y - m); x1 = min(44, x + size + m); y1 = min(44, y + size + m)''',
'''            it = items[i]; x, y = it["tile"]; size = it["size"]
            # 至少裁 4x4 格，保证 96px 下边缘清晰
            side = max(4, size + 2)
            pad = (side - size) // 2
            x0 = max(0, x - pad); y0 = max(0, y - pad)
            x1 = min(44, x0 + side); y1 = min(44, y0 + side)
            x0 = max(0, x1 - side); y0 = max(0, y1 - side)''')
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("montage 4x4 min patch")
