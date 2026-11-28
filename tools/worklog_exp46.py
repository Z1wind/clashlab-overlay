# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
with open(os.path.join(BASE, 'docs', 'WORKLOG.md'), 'a', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join([
        '',
        '## 持续实验（2026-11-28 20:00-20:20）',
        '- 分类器多seed集成+TTA：top1 94.1%（单模型 95.4%），TTA 无变化 → 不采用',
        '- 混合变体（修正偏移后重评，leaky）：位置精修 F1 .723→.739；TTA/占用后处理变差；诚实 CV 前4折精修 0.671 vs 基线 0.686 → 精修无增益，已停',
        '- 更强数据增强（透视+遮挡+颜色）：CV P56.3/R69.3/F1 .613/type 93.8 vs 基线 .658 → 增强过强有害，不采用',
        '- 结论：当前混合基线（P62.3/R71.0/F1 .658/type 91.8）仍最优；真正的提升来自 v1.7 的裁剪中心 bug 修复',
        '',
    ]))
print('worklog updated')