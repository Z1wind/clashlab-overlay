# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
with open(os.path.join(BASE, 'docs', 'WORKLOG.md'), 'a', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join([
        '',
        '## 实验：硬负样本门控（2026-11-28 20:40）',
        '- 负样本 50% 取建筑周围 2.2-4.5 格环带（墙/装饰），其余随机',
        '- 8 基 CV：P62.1 / R64.8 / F1 .625 / type 92.5%（基线 P62.3/R71.0/F1 .658）→ 无增益',
        '- 实验脚本：tools/train_hybrid_hardneg_cv.py；报告：out/hybrid_hardneg_report.json',
        '',
        '## 平台期总结（8 张数据，共验证 8 组方案）',
        '- 负结果：分类器集成/TTA、强增强、位置精修、占用后处理、6x6 上下文、硬负样本、网格分割检测器',
        '- 正结果：v1.7 裁剪中心 bug 修复（实际精度 62%→90%，b03）',
        '- 结论：数据量是唯一瓶颈；需要更多标注（目标 20-30 张）才能继续提升',
        '',
    ]))
print('worklog hardneg')