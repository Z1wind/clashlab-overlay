# -*- coding: utf-8 -*-
"""面板底板美化：竖向渐变 + 顶部琥珀渐变条 + 内高光。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "overlay", "runtime.py")
t = open(p, encoding="utf-8").read()
anchor = '''    dl.add_rect_filled(imgui.ImVec2(px, py), imgui.ImVec2(W, H),
                        col=imgui.color_convert_float4_to_u32(
                            imgui.ImVec4(*theme.PANEL_BG)),
                        rounding=0.0)
    dl.add_rect(imgui.ImVec2(px, py), imgui.ImVec2(W, H),
                col=imgui.color_convert_float4_to_u32(theme.PANEL_BORDER),
                rounding=0.0, thickness=1.5)'''
new = '''    # 竖向微渐变：顶部略亮、底部略沉，避免整块死板纯色
    _u = imgui.color_convert_float4_to_u32
    _bg = theme.PANEL_BG
    _top = theme._lift(_bg, 1.16)
    _bot = theme._lift(_bg, 0.88)
    dl.add_rect_filled_multi_color(
        imgui.ImVec2(px, py), imgui.ImVec2(W, H),
        _u(imgui.ImVec4(*_top)), _u(imgui.ImVec4(*_top)),
        _u(imgui.ImVec4(*_bot)), _u(imgui.ImVec4(*_bot)), rounding=0.0)
    # 顶部琥珀强调条（左亮右暗，像一条细高光）
    _bar_w = 3.0
    _accent = theme.ACCENT
    dl.add_rect_filled_multi_color(
        imgui.ImVec2(px, py), imgui.ImVec2(W, py + _bar_w),
        _u(imgui.ImVec4(*_accent)), _u(imgui.ImVec4(_accent[0], _accent[1], _accent[2], 0.35)),
        _u(imgui.ImVec4(_accent[0], _accent[1], _accent[2], 0.35)), _u(imgui.ImVec4(*_accent)),
        rounding=0.0)
    # 内高光（1px）+ 外描边
    dl.add_line(imgui.ImVec2(px, py + _bar_w), imgui.ImVec2(W, py + _bar_w),
                _u(imgui.ImVec4(1.0, 1.0, 1.0, 0.06)), 1.0)
    dl.add_rect(imgui.ImVec2(px, py), imgui.ImVec2(W, H),
                col=_u(imgui.ImVec4(*theme.PANEL_BORDER)),
                rounding=0.0, thickness=1.5)'''
if anchor in t:
    t = t.replace(anchor, new, 1)
    open(p, "w", encoding="utf-8", newline=chr(10)).write(t)
    print("panel chrome patched")
else:
    print("anchor miss")
