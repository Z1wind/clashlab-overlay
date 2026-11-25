# -*- coding: utf-8 -*-
"""把「44x44 网格从地图最外圈开始标（不是最外侧建筑/墙）」写进 UI 提示与文档。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"

def patch(rel, pairs):
    p = os.path.join(BASE, rel)
    txt = open(p, encoding="utf-8").read()
    changed = 0
    for old, new in pairs:
        if old in txt:
            txt = txt.replace(old, new)
            changed += 1
    if changed:
        open(p, "w", encoding="utf-8", newline="\n").write(txt)
    print(rel, "replacements:", changed)

patch("tools/annotate/index.html", [
    ('title="校准网格：拖动 4 个角点贴合草地（G）"',
     'title="校准网格：拖动 4 个角点贴合「地图最外圈格」边界，不是最外侧建筑/墙（G）"'),
    ('拖 4 个角点（上/右/下/左）对齐草地外沿；方向键 ±1px、Shift+方向键 ±10px；Enter 应用 / Esc 取消',
     '拖 4 个角点（上/右/下/左）对齐<b>整张 44×44 地图的最外圈格边界</b>（不是最外侧建筑/墙）；方向键 ±1px、Shift+方向键 ±10px；Enter 应用 / Esc 取消'),
    ('5. 若发现预填整体偏/斜（quad 不贴合草地），按 <kbd>G</kbd> 进「校准网格」：拖 4 个角点对齐外墙/草地四角',
     '5. 若发现预填整体偏/斜（quad 不贴合地图边界），按 <kbd>G</kbd> 进「校准网格」：拖 4 个角点对齐<b>整张地图最外圈格的四个角</b>（从最外圈格算起，不是从最外侧建筑或墙算起）'),
    ("校准网格：拖动 4 个角点（上/右/下/左）对齐草地外沿；方向键 ±1px，Shift+方向键 ±10px。应用后拖拽/保存都用新映射。",
     "校准网格：拖动 4 个角点（上/右/下/左）对齐整张地图最外圈格的边界（不是最外侧建筑/墙）；方向键 ±1px，Shift+方向键 ±10px。应用后拖拽/保存都用新映射。"),
    ("校准模式：拖动四角（上/右/下/左）贴合草地；方向键微调；Enter 应用 / Esc 取消",
     "校准模式：拖动四角（上/右/下/左）贴合地图最外圈格边界（不是外墙）；方向键微调；Enter 应用 / Esc 取消"),
])

patch("tools/annotate/README.md", [
    ("- quad 顺序 = 上、右、下、左，对应 tile (0,0)/(grid,0)/(grid,grid)/(0,grid)",
     "- quad 顺序 = 上、右、下、左，对应 tile (0,0)/(grid,0)/(grid,grid)/(0,grid)\n- 标定规则：44x44 网格覆盖整张地图的 44 格，四角 = 地图最外圈格的四个角（通常就是可建造草地/边界）；不要把角点贴到最外侧建筑或墙上，否则整体会缩一圈"),
])

patch("docs/教程.md", [
    ("- 自动检测草地边界做 44×44 标定，输出 bases/th16/07/base.png 和 layout_draft.json；",
     "- 自动检测草地边界做 44×44 标定，输出 bases/th16/07/base.png 和 layout_draft.json；\n- 标定口径：44×44 指整张地图的 44 格，四角取地图最外圈格的边界，不是最外侧建筑或墙；"),
])

patch("docs/TUTORIAL_en.md", [
    ("- Detects the grass boundary for a 44x44 calibration and writes bases/th16/07/base.png + layout_draft.json;",
     "- Detects the grass boundary for a 44x44 calibration and writes bases/th16/07/base.png + layout_draft.json;\n- Calibration rule: the 44x44 grid spans the whole map; the four corners are the outer edges of the outermost tile row/column, NOT the outermost building or wall."),
])
