# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
with open(os.path.join(BASE, 'docs', 'WORKLOG.md'), 'a', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join([
        '',
        '## v1.9 交付前全基准一致性检查（2026-11-28 21:40，leaky）',
        '- standard: P81.5 / R75.2 / type98.1 / 平均84栋 / 2.6s',
        '- recall:   P72.0 / R79.8 / type96.9 / 平均103栋 / 2.6s',
        '- precise:  P86.5 / R73.4 / type99.1 / 平均77栋 / 5.1s',
        '- 最弱项：b07 standard R0.61；b05 recall P0.50（误报多）→ 后续数据补 b05/b07 类分布',
        '- 脚本 out/logs/v19_allbases.log、tools/eval_v19_allbases.py',
        '',
    ]))
print('worklog v19 eval')