# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"

# 1) runtime fallback
p = os.path.join(BASE, "clashlab", "overlay", "runtime.py")
t = open(p, encoding="utf-8").read()
old = "    dl.add_rect_filled_multi_color(\n        imgui.ImVec2(px, py), imgui.ImVec2(W, H),\n        _u(imgui.ImVec4(*_top)), _u(imgui.ImVec4(*_top)),\n        _u(imgui.ImVec4(*_bot)), _u(imgui.ImVec4(*_bot)))"
new = "    try:\n        dl.add_rect_filled_multi_color(\n            imgui.ImVec2(px, py), imgui.ImVec2(W, H),\n            _u(imgui.ImVec4(*_top)), _u(imgui.ImVec4(*_top)),\n            _u(imgui.ImVec4(*_bot)), _u(imgui.ImVec4(*_bot)))\n    except TypeError:\n        # 不同 imgui_bundle 版本签名不一致：退化为纯色，避免 draw frame error\n        dl.add_rect_filled(imgui.ImVec2(px, py), imgui.ImVec2(W, H), _u(imgui.ImVec4(*_bg)))"
if old in t:
    t = t.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("runtime fallback ok")
else:
    print("runtime anchor miss")

# 2) pages
p2 = os.path.join(BASE, "clashlab", "overlay", "pages.py")
t2 = open(p2, encoding="utf-8").read()
t2 = t2.replace("def _btn(label, size, *, kind=\"sec\", active=False, disabled=False, key=None):",
                "def _btn(label, size, *, kind=\"sec\", active=False, disabled=False, key=None, tip=None):", 1)
t2 = t2.replace("        imgui.button(f\"{label}##{fid}\", size)\n        for _ in range(4):\n            imgui.pop_style_color()\n        return False",
                "        imgui.button(f\"{label}##{fid}\", size)\n        if tip and imgui.is_item_hovered():\n            imgui.set_tooltip(tip + \"（当前不可用）\")\n        for _ in range(4):\n            imgui.pop_style_color()\n        return False", 1)
t2 = t2.replace("    for _ in range(4):\n        imgui.pop_style_color()\n    return clicked",
                "    if tip and imgui.is_item_hovered():\n        imgui.set_tooltip(tip)\n    for _ in range(4):\n        imgui.pop_style_color()\n    return clicked", 1)
t2 = t2.replace("    loaded = bool(study_png)",
                "    loaded = bool(getattr(state, \"layout\", None) or getattr(state, \"Layout\", None))", 1)
t2 = t2.replace("else '未加载'", "else '未加载/点采集'")
open(p2, "w", encoding="utf-8", newline="\n").write(t2)
print("pages ok")
