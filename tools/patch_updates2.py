# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
zh = "## 最近更新（2026-11-25）\n\n- 半自动标注工具 tools/annotate：layout.json 预填 + 点选修正 + 自动保存；新增**网格校准（G）**——拖动 4 个角点对齐整张地图，44×44 网格按「地图最外圈格」起算（不是最外侧建筑/墙）。\n- tools/import_base.py：游戏里点开阵型链接 → 截屏 → 自动 44×44 标定 → 生成 base.png + layout_draft.json。\n- 标注 → 训练闭环：clashlab/recog_dataset.py + tools/train_from_annotations.py。\n- 城墙对称推理 clashlab/wall_symmetry.py；2D 化 clashlab/topdown.py；Windows + Python 3.13 的 CI。\n- base link 解码调研（见 docs/BASELINK_RESEARCH.md）；进度与下一步见 docs/NEXT_STEPS.md。\n\n"
en = "## Recent updates (2026-11-25)\n\n- Semi-automatic annotation tool tools/annotate: layout.json prefill + click-to-fix + autosave; new **grid calibration (G)** — drag 4 corners to fit the whole map (44x44 counts from the outermost map tile, not the outermost building/wall).\n- tools/import_base.py: open a shared base link in-game -> screenshot -> auto 44x44 calibration -> base.png + layout_draft.json.\n- Annotation -> training loop: clashlab/recog_dataset.py + tools/train_from_annotations.py.\n- Wall symmetry inference (clashlab/wall_symmetry.py), 2D top-down renderer (clashlab/topdown.py), CI on Windows + Python 3.13.\n- Base-link decoding research (docs/BASELINK_RESEARCH.md), progress and next steps in docs/NEXT_STEPS.md.\n\n"

def patch(rel, block, marker):
    p = os.path.join(BASE, rel)
    t = open(p, encoding='utf-8').read()
    if marker in t:
        print('skip', rel); return
    i = t.find(chr(10) + '## ')
    if i < 0:
        print('no section', rel); return
    t = t[:i+1] + block + t[i+1:]
    open(p, 'w', encoding='utf-8', newline=chr(10)).write(t)
    print('patched', rel, 'bytes', len(t.encode()))

patch('README.md', zh, '最近更新（2026-11-25）')
patch('README.en.md', en, 'Recent updates (2026-11-25)')
