# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
def c(s): return BT + s + BT
doc = ("# ClashLab v0.3.5（2026-11-27）\n\n"
       "## 新增\n"
       "- **内置标注器服务** " + c("clashlab/annotator.py") + " + 面板「启动标注器」按钮（无游戏时面板也能独立打开）\n"
       "- **战斗模拟升级**：英雄/法术/援军修正、TH 缩放、多配比对比（sim_attack --compare）\n"
       "- **实验性自动候选**：/candidates + 标注器「自动候选」按钮（当前分类器退化，仅实验，页面已标注）\n\n"
       "## 验证\n"
       "- 350 项测试 OK；面板实机点击拉起标注器（HTTP 200）；06 阵三配比对比：ground 3星95%、air 3星98%、hybrid 3星88%\n\n"
       "## 已知问题\n"
       "- 自动候选在真实图上分类器退化（几乎全是 gold-mine），不可用于生产；需真实负样本训练\n"
       "- 模拟仍为启发式（非游戏真实引擎）\n\n"
       "> 非官方工具；请自行评估 ToS 风险。\n")
open(os.path.join(BASE, "docs", "RELEASE_v0.3.5.md"), "w", encoding="utf-8", newline="\n").write(doc)
print("notes written")
