# -*- coding: utf-8 -*-
"""修 topdown 颜色（BGR）与图例/边距。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "topdown.py")
t = open(p, encoding="utf-8").read()

old_colors = '''CATEGORY_COLOR = {
    "town-hall": (255, 215, 0),
    "defense": (70, 130, 220),
    "storage": (60, 180, 75),
    "army": (180, 160, 60),
    "other": (160, 160, 160),
}'''
new_colors = '''# 注意：cv2 是 BGR 序
CATEGORY_COLOR = {
    "town-hall": (0, 200, 255),      # 琥珀金
    "defense": (235, 150, 70),       # 钢蓝
    "storage": (90, 200, 120),       # 薄荷绿
    "army": (200, 210, 120),         # 沙金
    "other": (160, 160, 160),        # 灰
}'''
if old_colors in t:
    t = t.replace(old_colors, new_colors)
    print("colors fixed")

# 尺寸/边距：底部加图例带
t = t.replace('    margin, hud_h = 26, 54\n    w = h = g * cell + margin * 2',
              '    margin, hud_h, legend_h = 26, 54, 40\n    w = g * cell + margin * 2\n    h = g * cell + margin + hud_h + legend_h')
t = t.replace('_rounded_rect(img, margin - 6, margin + hud_h - 6, w - margin + 6, h - margin + 6, 12, (22, 28, 36), -1)',
              '_rounded_rect(img, margin - 6, margin + hud_h - 6, w - margin + 6, margin + hud_h + g * cell + 6, 12, (22, 28, 36), -1)')
t = t.replace('    _rounded_rect(img, 2, 2, w - 3, h - 3, 16, (58, 70, 86), 2)',
              '    _rounded_rect(img, 2, 2, w - 3, h - 3, 16, (58, 70, 86), 2)\n    # 图例带')
t = t.replace('''    # 图例
    lx, ly = margin + 10, h - margin - 2
    for label, ckey in (("大本营", "town-hall"), ("防御", "defense"), ("资源", "storage"),
                        ("兵营", "army"), ("其它", "other")):
        col = CATEGORY_COLOR[ckey]
        _rounded_rect(img, lx, ly - 12, lx + 14, ly + 2, 3, col, -1)
        _text_outline(img, label, (lx + 20, ly), 0.38, (210, 220, 232))
        lx += 78''',
'''    # 图例（cv2 不渲染中文，用英文；底部独立带，不压地图）
    lx, ly = margin + 10, h - 16
    cv2.line(img, (margin + 6, ly - 24), (w - margin - 6, ly - 24), (48, 58, 72), 1, cv2.LINE_AA)
    for label, ckey in (("Town Hall", "town-hall"), ("Defense", "defense"), ("Storage", "storage"),
                        ("Army", "army"), ("Other", "other")):
        col = CATEGORY_COLOR[ckey]
        _rounded_rect(img, lx, ly - 12, lx + 14, ly + 2, 3, col, -1)
        _text_outline(img, label, (lx + 20, ly), 0.40, (205, 216, 230))
        lx += 104''')

# 建筑标签：只在大格子上画，居中
t = t.replace('''        short = tp.replace("-", " ")[:7]
        _text_outline(img, short, (bx + 5, by + bw // 2 + 9), 0.30, (245, 248, 252))''',
'''        if bw >= 3 * cell:
            short = tp.replace("-", " ")[:8]
            (tw_, th_), _ = cv2.getTextSize(short, cv2.FONT_HERSHEY_SIMPLEX, 0.32, 1)
            _text_outline(img, short, (bx + (bw - tw_) // 2, by + bw // 2 + 4), 0.32, (245, 248, 252))''')
open(p, "w", encoding="utf-8", newline=chr(10)).write(t)
print("topdown fixed")
