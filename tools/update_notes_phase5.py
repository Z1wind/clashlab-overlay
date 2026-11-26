# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
BT = chr(96)
def c(s): return BT + s + BT
upd = ('## 最近更新（2026-11-26）' + chr(10) + chr(10) +
       '- **全大本营支持（TH1–TH19）**：' + c('clashlab/th_data.py') + ' + ' + c('knowledge/th_ruleset.json') + '（reviewed ruleset：尺寸/等级/解锁精确，TH17–19 hp/dps 低置信外推），文档 ' + c('docs/TH_SUPPORT.md') + '。' + chr(10) +
       '- **布阵 → 兵种搭配推荐**：' + c('clashlab/strategy.py') + ' 按弱点判定（对空缺口/大本营偏心/隔间密集）给 3 条 meta 搭配与投放步骤，附 YouTube 搜索入口（不存储第三方内容）；数据 ' + c('knowledge/strategies.json') + '；文档 ' + c('docs/STRATEGY.md') + '。' + chr(10) +
       '- **放兵点 → 放兵线/区域**：' + c('clashlab/deploy.py') + ' 枚举 12 条撒兵线 + 4 个区域并挑摧毁率最高；base 03 实测 **17.9% → 24.7%**；文档 ' + c('docs/DEPLOY.md') + '。' + chr(10) +
       '- **四角回归模型（自动标定兜底）**：' + c('clashlab/quad_model.py') + ' + ' + c('models/quad_model.pt') + '，勇气来自社区阵图 + 草地边界伪标签（51/57 自动标注成功）；文档 ' + c('docs/QUAD_MODEL.md') + '。' + chr(10) +
       '- 兵棋推演/QA 矩阵/识别模型见上一条更新。' + chr(10) + chr(10))
p = os.path.join(BASE, 'README.md')
t = open(p, encoding='utf-8').read()
i = t.find('## 最近更新（2026-11-26）')
j = t.find('## ', i + 5) if i >= 0 else -1
if i >= 0 and j > i:
    t = t[:i] + upd + t[j:]
    open(p, 'w', encoding='utf-8', newline=chr(10)).write(t)
    print('README zh updated')
else:
    print('README zh miss', i, j)
upd_en = ('## Recent updates (2026-11-26)' + chr(10) + chr(10) +
          '- **TH1–TH19 support**: ' + c('clashlab/th_data.py') + ' + ' + c('knowledge/th_ruleset.json') + ' (reviewed ruleset: sizes/levels/unlocks exact; TH17-19 hp/dps low-confidence extrapolation); see ' + c('docs/TH_SUPPORT.md') + '.' + chr(10) +
          '- **Layout -> army recommendation**: ' + c('clashlab/strategy.py') + ' picks 3 meta compositions from weakness signals, with deployment steps and YouTube search links; data in ' + c('knowledge/strategies.json') + '; docs ' + c('docs/STRATEGY.md') + '.' + chr(10) +
          '- **Spawn point -> spawn line/region**: ' + c('clashlab/deploy.py') + ' enumerates 12 lines + 4 regions and picks the best; base 03 measured **17.9% -> 24.7%**; docs ' + c('docs/DEPLOY.md') + '.' + chr(10) +
          '- **Quad regression model (calibration fallback)**: ' + c('clashlab/quad_model.py') + ' + ' + c('models/quad_model.pt') + ' trained on community images with grass-boundary pseudo-labels (51/57 auto-labelled); docs ' + c('docs/QUAD_MODEL.md') + '.' + chr(10) + chr(10))
p2 = os.path.join(BASE, 'README.en.md')
t2 = open(p2, encoding='utf-8').read()
i2 = t2.find('## Recent updates (2026-11-26)')
j2 = t2.find('## ', i2 + 5) if i2 >= 0 else -1
if i2 >= 0 and j2 > i2:
    t2 = t2[:i2] + upd_en + t2[j2:]
    open(p2, 'w', encoding='utf-8', newline=chr(10)).write(t2)
    print('README en updated')
else:
    print('README en miss', i2, j2)
p3 = os.path.join(BASE, 'CHANGELOG.md')
t3 = open(p3, encoding='utf-8').read()
if 'TH1–TH19' not in t3:
    add = ('## v0.2.0 (unreleased)' + chr(10) + chr(10) +
           '- TH1–TH19 数据层（reviewed ruleset）与 assets.stats 委托；' + chr(10) +
           '- 布阵 → 兵种搭配推荐（弱点判定 + 投放步骤 + YouTube 搜索入口）；' + chr(10) +
           '- 放兵线/区域优化（候选枚举 + 自动挑选，base03 17.9%→24.7%）；' + chr(10) +
           '- 四角回归模型（社区阵图 + 草地伪标签，import_base 兜底）。' + chr(10) + chr(10))
    t3 = t3.replace('## v0.1.2 (unreleased)', add + '## v0.1.2 (unreleased)', 1)
    open(p3, 'w', encoding='utf-8', newline=chr(10)).write(t3)
    print('CHANGELOG updated')
