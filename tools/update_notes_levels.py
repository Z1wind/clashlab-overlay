# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
def c(s): return BT + s + BT
# README zh：在最近更新顶部插入等级条目
p = os.path.join(BASE, "README.md")
t = open(p, encoding="utf-8").read()
if "等级体系" not in t:
    add = ('- **等级体系（新）**：' + c('clashlab/levels.py') + ' + ' + c('clashlab/th_data.py') + ' 支持建筑/兵种/英雄等级；推演实测「低等级兵/英雄」让摧毁率从 18.95% 掉到 8.55%，「低等级敌方建筑」升到 21.05%；说明见 ' + c('docs/LEVELS.md') + '。' + chr(10))
    anchor = "- **全大本营支持（TH1–TH19）**"
    if anchor in t:
        t = t.replace(anchor, add + anchor, 1)
        open(p, "w", encoding="utf-8", newline=chr(10)).write(t)
        print("readme zh updated")
    else:
        print("zh anchor miss")
# README en
p2 = os.path.join(BASE, "README.en.md")
t2 = open(p2, encoding="utf-8").read()
if "Level system" not in t2:
    add2 = ('- **Level system (new)**: ' + c('clashlab/levels.py') + ' + ' + c('clashlab/th_data.py') + ' take building/troop/hero levels; measured: low-level troops drop destruction from 18.95% to 8.55%, low-level enemy buildings raise it to 21.05%; see ' + c('docs/LEVELS.md') + '.' + chr(10))
    a2 = "- **TH1–TH19 support**"
    if a2 in t2:
        t2 = t2.replace(a2, add2 + a2, 1)
        open(p2, "w", encoding="utf-8", newline=chr(10)).write(t2)
        print("readme en updated")
    else:
        print("en anchor miss")
# CHANGELOG
p3 = os.path.join(BASE, "CHANGELOG.md")
t3 = open(p3, encoding="utf-8").read()
if "等级体系" not in t3:
    add3 = '- 等级体系：建筑/兵种/英雄等级参与推演（实测低配兵摧毁率 18.95%→8.55%）；' + chr(10)
    t3 = t3.replace("## v0.2.0 (unreleased)" + chr(10), "## v0.2.0 (unreleased)" + chr(10) + add3, 1)
    open(p3, "w", encoding="utf-8", newline=chr(10)).write(t3)
    print("changelog updated")
