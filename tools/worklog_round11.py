# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
with open(os.path.join(BASE, 'docs', 'WORKLOG.md'), 'a', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join([
        '',
        '## 类型级错误分析 + 发布脚本（2026-11-28 21:45）',
        '- 最差召回（leaky 8 基准，标准档）：dark-elixir-drill 0.48、barracks/spell-factory/dark-spell-factory/pet-house 0.50、elixir-collector 0.54、elixir-storage 0.56、gold-mine 0.62',
        '- 类型混淆极少：builder-hut<->helper-hut x5+2、scattershot->builder-hut x1、army-camp->mortar x1',
        '- 结论：瓶颈是「小建筑密集排布时的门控漏检」，不是分类；新标注优先补收集器/储藏/训练营密集阵',
        '- 标准档阈值 leaky 扫描确认最优：(0.85/0.85) P.815/R.752/F1 .782；降阈值只换 +0.4pt 召回、丢 1.5pt 精度',
        '- 新增 tools/release_from_labels.ps1：一条命令 = 质检->重训->质量闸门(失败回滚)->打包->上传；语法校验通过（未跑全流程，等新数据）',
        '',
    ]))
print('worklog round11')