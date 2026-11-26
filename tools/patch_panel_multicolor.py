# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "overlay", "runtime.py")
t = open(p, encoding="utf-8").read()
n = t.count("rounding=0.0)\n    # 顶部琥珀强调条")
t = t.replace('''        _u(imgui.ImVec4(*_top)), _u(imgui.ImVec4(*_top)),
        _u(imgui.ImVec4(*_bot)), _u(imgui.ImVec4(*_bot)), rounding=0.0)''',
'''        _u(imgui.ImVec4(*_top)), _u(imgui.ImVec4(*_top)),
        _u(imgui.ImVec4(*_bot)), _u(imgui.ImVec4(*_bot)))''')
t = t.replace('''        _u(imgui.ImVec4(*_accent)), _u(imgui.ImVec4(_accent[0], _accent[1], _accent[2], 0.35)),
        _u(imgui.ImVec4(_accent[0], _accent[1], _accent[2], 0.35)), _u(imgui.ImVec4(*_accent)),
        rounding=0.0)''',
'''        _u(imgui.ImVec4(*_accent)), _u(imgui.ImVec4(_accent[0], _accent[1], _accent[2], 0.35)),
        _u(imgui.ImVec4(_accent[0], _accent[1], _accent[2], 0.35)), _u(imgui.ImVec4(*_accent)))''')
open(p, "w", encoding="utf-8", newline=chr(10)).write(t)
print("patched multi_color calls")
