# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
with open(os.path.join(BASE, 'docs', 'WORKLOG.md'), 'a', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join([
        '',
        '## 实验：半格相位候选合并（2026-11-28 21:25）',
        '- leaky 8 基准：整数格 P81.5/R75.2/F1 .780；半格 P82.5/R75.2/F1 .783；合并 P80.4/R82.3/F1 .811（方向性 +3pt）',
        '- 诚实 8 折 CV：合并后 P69.3/R62.2/F1 .643/type 95.0（基线 P62.3/R71.0/F1 .658/type 91.8）',
        '- 结论：半格合并能提精度 +7pt、类型 +3pt，但召回 -9pt、F1 略降；暂不替换标准档，保留为「精确档」可选方案',
        '- 代码已预留 preannotate_core.detect(phases=(0.0,)) 参数，可随时启用',
        '- 脚本：tools/half_offset_scan.py、tools/train_hybrid_halfphase_cv.py、tools/mk_halfphase_cv.py',
        '',
    ]))
print('worklog halfphase')