# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"

# ---------- 1) runtime: 多色渐变调用加兼容兜底 ----------
p = os.path.join(BASE, "clashlab", "overlay", "runtime.py")
t = open(p, encoding="utf-8").read()
old = '''    dl.add_rect_filled_multi_color(
        imgui.ImVec2(px, py), imgui.ImVec2(W, H),
        _u(imgui.ImVec4(*_top)), _u(imgui.ImVec4(*_top)),
        _u(imgui.ImVec4(*_bot)), _u(imgui.ImVec4(*_bot)))'''
new = '''    try:
        dl.add_rect_filled_multi_color(
            imgui.ImVec2(px, py), imgui.ImVec2(W, H),
            _u(imgui.ImVec4(*_top)), _u(imgui.ImVec4(*_top)),
            _u(imgui.ImVec4(*_bot)), _u(imgui.ImVec4(*_bot)))
    except TypeError:
        # 某些 imgui_bundle 版本签名不同：退化为纯色，避免每帧 draw frame error
        dl.add_rect_filled(imgui.ImVec2(px, py), imgui.ImVec2(W, H), _u(imgui.ImVec4(*_bg)))'''
if old in t:
    t = t.replace(old, new, 1)
    print("multi_color fallback")
open(p, "w", encoding="utf-8", newline="\n").write(t)

# ---------- 2) pages: 按钮 tooltip + 状态行诊断 ----------
p2 = os.path.join(BASE, "clashlab", "overlay", "pages.py")
t2 = open(p2, encoding="utf-8").read()
old_btn = '''def _btn(label, size, *, kind="sec", active=False, disabled=False, key=None):'''
new_btn = '''def _btn(label, size, *, kind="sec", active=False, disabled=False, key=None, tip=None):'''
t2 = t2.replace(old_btn, new_btn, 1)
old_dis = '''        imgui.button(f"{label}##{fid}", size)
        for _ in range(4):
            imgui.pop_style_color()
        return False'''
new_dis = '''        imgui.button(f"{label}##{fid}", size)
        if tip and imgui.is_item_hovered():
            imgui.set_tooltip(tip + "（当前不可用）")
        for _ in range(4):
            imgui.pop_style_color()
        return False'''
t2 = t2.replace(old_dis, new_dis, 1)
old_ret = '''    for _ in range(4):
        imgui.pop_style_color()
    return clicked'''
new_ret = '''    if tip and imgui.is_item_hovered():
        imgui.set_tooltip(tip)
    for _ in range(4):
        imgui.pop_style_color()
    return clicked'''
t2 = t2.replace(old_ret, new_ret, 1)

# 状态行：阵型是否真的加载（不再用 study_png 误导）
t2 = t2.replace("    loaded = bool(study_png)",
                "    loaded = bool(getattr(state, \"layout\", None) or getattr(state, \"Layout\", None))", 1)
t2 = t2.replace('right = _L(ready, f"阵型 {\\'已加载\\' if loaded else \\'未加载\\'} · 候选 {cand_n}",',
                'right = _L(ready, f"阵型 {\\'已加载\\' if loaded else \\'未加载（点采集）\\'} · 候选 {cand_n}",')
open(p2, "w", encoding="utf-8", newline="\n").write(t2)
print("pages patched")
