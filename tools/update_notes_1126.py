# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
BT = chr(96)
def c(s):
    return BT + s + BT

# ML doc numbers
p = os.path.join(BASE, 'docs', 'ML_FEASIBILITY.md')
t = open(p, encoding='utf-8').read()
old = ('| 数据 | within-5fold | LOBO |' + chr(10) + '|---|---|---|' + chr(10) +
       '| 原始 layout | 0.435 | 未跑完 |' + chr(10) +
       '| **人工标注** | **0.734** | **0.641** |' + chr(10) +
       '| 历史基线（3 阵 107 样本） | 0.523 | 0.520 |')
new = ('| 数据 / 配置 | within-5fold | LOBO | 说明 |' + chr(10) + '|---|---|---|---|' + chr(10) +
       '| 原始 layout（60 epoch 快速对照） | 0.435 | 未跑完 | tools/train_from_annotations.py |' + chr(10) +
       '| **人工标注 + 本仓 checkpoint（30 epoch）** | **0.630** | **0.477** | models/metrics.json 实测 |' + chr(10) +
       '| 人工标注 + 充分训练（60–100 epoch） | 0.734 | 0.641 | 早前实验，同协议不同 epoch |' + chr(10) +
       '| 历史基线（3 阵 107 样本） | 0.523 | 0.520 | 旧实验 |')
if old in t:
    t = t.replace(old, new)
else:
    print('ML table anchor miss')
t = t.replace('- **可行性成立**：27px 外观对「类别」有可学信号（LOBO ≈0.6 vs 基线 0.117，且远超历史 0.520）。',
              '- **可行性成立**：27px 外观对「类别」有可学信号——checkpoint（30 epoch）within 0.630 / LOBO 0.477，显著高于多数类基线 0.117；充分训练（60–100 epoch）可到 0.734 / 0.641。')
t = t.replace('复现出的数字若与 0.734/0.641 有出入，属正常波动（seed、torch 版本、线程数），以 ' + c('models/metrics.json') + ' 为准。',
              '复现出来的数字以 ' + c('models/metrics.json') + ' 为准；epoch 数影响很大（30 epoch → 0.630/0.477，60–100 epoch → 0.734/0.641）。')
open(p, 'w', encoding='utf-8', newline=chr(10)).write(t)
print('ML doc updated')

# README zh
upd = ('## 最近更新（2026-11-26）' + chr(10) + chr(10) +
       '- **兵棋推演** ' + c('clashlab/wargame.py') + '：军队构成 + 投放点 → 确定性 tick 战斗模拟 + Monte Carlo 摧毁率分布（base 03 实测 mean 15.5%，最佳投放点 22.1%），CLI 见 ' + c('tools/wargame_cli.py') + '。' + chr(10) +
       '- **实机 UI 验证**：' + c('tools/qa_e2e.py') + ' 一条命令跑 7 项矩阵（HUD/PANEL × 有/无布局、页签切换、缩放重标定、exe 自检），本机实跑 **7/7 PASS**，报告 ' + c('docs/QA_E2E.md') + '。' + chr(10) +
       '- **机器学习可行性**：' + c('tools/train_save_model.py') + ' 训练并保存 ' + c('models/recog_27px.pt') + '（within 0.630 / LOBO 0.477；充分训练可到 0.734 / 0.641），推理接口 ' + c('clashlab/recog_model.py') + '，报告 ' + c('docs/ML_FEASIBILITY.md') + '。' + chr(10) +
       '- 新增四角标注工具 ' + c('tools/label_corners/') + '（给自动标定模型造数据）。' + chr(10) + chr(10))
p2 = os.path.join(BASE, 'README.md')
t2 = open(p2, encoding='utf-8').read()
i = t2.find('## 最近更新（2026-11-25）')
j = t2.find('## ', i + 5) if i >= 0 else -1
if i >= 0 and j > i:
    t2 = t2[:i] + upd + t2[j:]
    open(p2, 'w', encoding='utf-8', newline=chr(10)).write(t2)
    print('README zh updated')
else:
    print('README zh miss', i, j)

# README en
upd_en = ('## Recent updates (2026-11-26)' + chr(10) + chr(10) +
       '- **Wargame simulation** (' + c('clashlab/wargame.py') + '): army + spawn -> deterministic tick battle sim + Monte Carlo destruction distribution (base 03 mean 15.5%, best spawn 22.1%); CLI in ' + c('tools/wargame_cli.py') + '.' + chr(10) +
       '- **In-game UI verification**: ' + c('tools/qa_e2e.py') + ' runs a 7-case matrix (HUD/PANEL with and without layout, tab switch, resize recalibration, exe self-check); 7/7 PASS on this machine; report ' + c('docs/QA_E2E.md') + '.' + chr(10) +
       '- **ML feasibility**: ' + c('tools/train_save_model.py') + ' trains and saves ' + c('models/recog_27px.pt') + ' (within 0.630 / LOBO 0.477; 0.734 / 0.641 with longer training); inference ' + c('clashlab/recog_model.py') + '; report ' + c('docs/ML_FEASIBILITY.md') + '.' + chr(10) +
       '- New corner-labeling tool ' + c('tools/label_corners/') + ' for auto-calibration data.' + chr(10) + chr(10))
p3 = os.path.join(BASE, 'README.en.md')
t3 = open(p3, encoding='utf-8').read()
i3 = t3.find('## Recent updates (2026-11-25)')
j3 = t3.find('## ', i3 + 5) if i3 >= 0 else -1
if i3 >= 0 and j3 > i3:
    t3 = t3[:i3] + upd_en + t3[j3:]
    open(p3, 'w', encoding='utf-8', newline=chr(10)).write(t3)
    print('README en updated')
else:
    print('README en miss', i3, j3)

# CHANGELOG
p4 = os.path.join(BASE, 'CHANGELOG.md')
t4 = open(p4, encoding='utf-8').read()
if '## v0.1.2' not in t4:
    add = ('## v0.1.2 (unreleased)' + chr(10) + chr(10) +
           '- wargame 引擎与 CLI：确定性兵棋推演 + Monte Carlo 摧毁率；' + chr(10) +
           '- qa_e2e 实机 UI 矩阵（本机 7/7 PASS）与报告；' + chr(10) +
           '- 识别模型训练/推理/可行性报告（models/recog_27px.pt、docs/ML_FEASIBILITY.md）；' + chr(10) +
           '- 四角标注工具 tools/label_corners/。' + chr(10))
    t4 = t4.replace('## v0.1.1 (unreleased)', add + chr(10) + '## v0.1.1 (unreleased)', 1)
    open(p4, 'w', encoding='utf-8', newline=chr(10)).write(t4)
    print('CHANGELOG updated')
