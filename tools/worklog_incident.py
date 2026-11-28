# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
with open(os.path.join(BASE, 'docs', 'WORKLOG.md'), 'a', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join([
        '',
        '## 事故与修复：重训模型退化（2026-11-28 20:50-21:00）',
        '- 现象：用 train_hybrid_full.py 重训后，b03 预标注 pred 从 72 掉到 12（召回 71%→13%），连训 3 次均退化',
        '- 处理：从 v1.7 EXE（PyInstaller CArchive）提取回好模型 models_good_v17，恢复后 b03 恢复 P90.3/R71.4/type100',
        '- 为防再次覆盖：重训加质量闸门（标准模式 pred>=50 否则回滚）',
        '- 根因修复：新写 tools/train_hybrid_final.py（复用 CV 已验证训练流程），产出 b03 标准 P84.0/R86.8/type97.5、多标 R92.3',
        '- 旧 train_hybrid_full.py 弃用；新流程：label_qa → train_hybrid_final → export_hybrid_onnx → 质量验证',
        '',
    ]))
print('worklog incident')