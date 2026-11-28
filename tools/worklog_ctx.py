# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
with open(os.path.join(BASE, 'docs', 'WORKLOG.md'), 'a', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join([
        '',
        '## 实验：门控 6x6 上下文（2026-11-28 20:25）',
        '- 门控看 6x6 格上下文（其余同混合方案），前 6 折 F1 0.622/0.626/0.663/0.601/0.525/0.559',
        '- 对比基线 4x4：0.616/0.726/0.766/0.636/0.738/0.711 → 更差，已终止',
        '- 结论：4x4 上下文足够；当前最优仍是混合基线 + v1.7 裁剪修复',
        '',
    ]))
print('worklog ctx')