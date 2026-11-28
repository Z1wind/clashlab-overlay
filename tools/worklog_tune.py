# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
with open(os.path.join(BASE, 'docs', 'WORKLOG.md'), 'a', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join([
        '',
        '## 阈值/NMS 调优（2026-11-28 21:15）',
        '- 阈值网格 CV（8 折）：当前 standard(0.85/0.85) P.648/R.630/F1 .639；最优 F1 在 (0.70/0.85) P.608/R.688/F1 .645（仅 +0.006，暂不改）',
        '- recall 模式 (0.70/0.70)：P.484/R.795（召回最高，误报多）',
        '- NMS 去重系数扫描（leaky 8 基准）：0.70/0.85/1.00 会残留重复框（pred 134-141），1.15 最佳 F1 .774/pred 86，1.30 略降 → 保持 1.15',
        '- 结论：v1.8 参数已接近当前数据的最优，无需再发版',
        '- 产物：out/mode_threshold_grid.json、out/logs/nms_sweep.log、tools/tune_modes_cv.py、tools/nms_sweep.py',
        '',
    ]))
print('worklog tune')