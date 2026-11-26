# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
p = os.path.join(BASE, 'docs', 'ROADMAP.md')
t = open(p, encoding='utf-8').read()
add = chr(10).join([
    '',
    '## 第四阶段（2026-11-26 起，用户新需求）',
    '',
    '1. **全大本营支持（TH1–TH19）**：`clashlab/th_data.py` 逐档数据 + 可信度标注；`assets.stats(name, th)` 委托该表；识别模型目前仅覆盖 TH16 的 19 类，其他档依赖标注数据。',
    '2. **布阵 → 兵种搭配推荐 + 联网打法 + 视频入口**：`clashlab/strategy.py` 由弱点驱动推荐（空军/地面/英雄切入），附投放步骤与 YouTube 搜索链接（不抓取第三方内容）；数据 `knowledge/strategies.json`。',
    '3. **后续（未开始）**：战术卡与英雄装备使用攻略（`knowledge/hero_equipment.json` 骨架先行，UI 接入待定）。',
    '',
    '## 已知限制（持续维护）',
    '',
    '- 兵棋推演数值为近似表，只做相对排序，未与真实战报校准；',
    '- 实机 QA 中物理鼠标点击未实测（系统注入被冻结），页签切换用进程内事件注入验证；',
    '- TH17–19 的建筑数值部分来自公开资料且 confidence 较低，导入/评分前请看 `docs/TH_SUPPORT.md`。',
    ''
])
if '第四阶段' not in t:
    t = t.rstrip() + chr(10) + add
    open(p, 'w', encoding='utf-8', newline=chr(10)).write(t)
    print('roadmap appended, bytes', len(t.encode()))
else:
    print('already present')
