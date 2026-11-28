# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
with open(os.path.join(BASE, 'docs', 'WORKLOG.md'), 'a', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join([
        '',
        '## 18 折 CV 异常 + 8 折抽样替代（2026-11-29 01:00）',
        '- 全量 18 折 CV 跑到第 6 折后 27 分钟无输出（进程仍占 GPU/CPU），判定单折病态慢速，已终止',
        '- 前 6 折 F1：0.667/0.729/0.709/0.671/0.498/0.663，均值 0.656（8 张版 0.658）',
        '- 改为 8 折代表性抽样：b01,b02,b03,b05,b08,b10,b14,b20 → out/logs/hybrid_subset_cv.log',
        '- 18 张数据覆盖：36 类全覆盖、1633 栋、每类>=10 例（无稀有类缺口）',
        '- 瓶颈：密集阵小建筑（收集器/储藏）定位，不是分类',
        '',
    ]))
print('worklog cv anomaly')