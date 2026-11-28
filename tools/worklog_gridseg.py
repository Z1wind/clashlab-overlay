# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
with open(os.path.join(BASE, 'docs', 'WORKLOG.md'), 'a', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join([
        '',
        '## 实验：网格分割检测器原型（2026-11-28 20:35）',
        '- 方案：四角规范化 512x512 输入 → U-Net → 44x44 类型图（一次前向替代 1600 次滑窗）',
        '- 8 基留一结果：prec 0.368 / recall 0.103 / f1 0.159 / type 0.843',
        '- 结论：8 张数据远不足以训分割检测（稀疏正样本 + 过拟合）；需 40+ 张再试，当前不采用',
        '- 脚本：tools/train_grid_seg_cv.py；报告：out/grid_seg_report.json',
        '',
    ]))
print('worklog grid seg')