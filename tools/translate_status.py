# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "overlay", "pages.py")
t = open(p, encoding="utf-8").read()
t = t.replace('imgui.text_colored(imgui.ImVec4(*theme.ACCENT), f"面板 实时={live_txt}")',
              'imgui.text_colored(imgui.ImVec4(*theme.ACCENT), _L(ready, f"面板 实时={live_txt}", f"Panel · {live_txt}"))', 1)
t = t.replace('f"实时={\'开\' if live else \'演练\'}"',
              '_L(ready, f"实时={\'开\' if live else \'演练\'}", f"Live={\'on\' if live else \'dry\'}")', 1)
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("status strings translated")
