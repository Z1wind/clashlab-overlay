# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
with open(os.path.join(BASE, 'docs', 'WORKLOG.md'), 'a', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join([
        '',
        '## 18 张标注重训 + v2.1 发布（2026-11-29 00:15）',
        '- 用户新提供 b10/b11/b12/b14/b15/b16/b17/b18/b19/b20 共 10 张（缺 b09/b13，不影响）',
        '- label_qa：10/10 PASS（bld 88-93，types 33-36，align 1.97-3.08）',
        '- 全量 18 张重训（train_hybrid_final.py）：b03 训练集内 标准 P91.8/R85.7/type98.7；多标 P84.8/R92.3；少错 P94.2/R71.4',
        '- 对比 8 张版：标准 P84.0→91.8（+7.8pt），召回持平 → 误报明显减少',
        '- v2.1 EXE：106,491,120 bytes md5 10B01A3F3FC15781B9082CC093DF26EE sha256 082b7cb8…77b780（Release digest 一致）',
        '- 打包 smoke：标准 85 / 多标 100 / 少错 77；补充预标注 existing=10 → 75',
        '- 18 折诚实 CV 进行中（前 3 折 F1 0.667/0.729/0.709，均值 0.702 vs 8 张 .658）',
        '- 旧模型备份：models/_good_v20（可回滚）',
        '',
    ]))
print('worklog v21')