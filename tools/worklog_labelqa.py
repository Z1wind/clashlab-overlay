# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
with open(os.path.join(BASE, 'docs', 'WORKLOG.md'), 'a', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join([
        '',
        '## 标注质检工具 label_qa.py（2026-11-28 20:40）',
        '- 检查：version/corners/图片存在/建筑数/tile 范围/重复/缺类型/对齐 ratio（标注点纹理能量 vs 随机位置）',
        '- 当前 8 张全部 PASS，对齐 ratio 2.53-4.00（b01/b02 重标后 3.20/3.05，修复前仅 ~1.0-1.2）',
        '- 后续用户新标注可直接跑：python tools/label_qa.py --labels "a.json;b.json"',
        '',
    ]))
print('worklog label qa')