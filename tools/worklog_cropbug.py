# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
with open(os.path.join(BASE, 'docs', 'WORKLOG.md'), 'a', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join([
        '',
        '## Bug 修复：推理裁剪中心偏移 0.5 格（2026-11-28 19:50）',
        '- 训练时 warp(cx,cy) 的窗口中心 = cx+0.5；preannotate_core 推理却传 cx+0.5，实际中心 cx+1.0',
        '- 影响：EXE 内 v1.5/v1.6 预标注精度明显低于 CV（b03 同阈值 精度约 62% vs 修复后 90%）',
        '- 修复：_crop(img, cal, cx, cy, size)，与训练一致；已在 v1.7 重建',
        '- 修复后 b03（训练集内）实测：标准 P0.903/R0.714/type 1.0；多标 P0.852/R0.824/type 0.96；少错 P0.932/R0.604/type 1.0',
        '',
    ]))
print('worklog updated')