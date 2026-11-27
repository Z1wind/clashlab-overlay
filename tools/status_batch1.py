# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
def c(s): return BT + s + BT
p = os.path.join(BASE, "docs", "STATUS.md")
t = open(p, encoding="utf-8").read()
add = ("\n## 🚀 2026-11-27：本地路线第一批（P1 布局/规则层 + 一键入口）\n\n"
       "- " + c("clashlab/layout_grid.py") + "：44×44 逐格模型（墙折线/成对线段两种格式自动识别），"
       "提供隔间(flood fill)/孤立墙/大本是否被墙包/结构校验；wall 数据不完整时标 " + c("wall_confidence=low") + "\n"
       "- " + c("clashlab/layout_rules.py") + "：8 条可解释规则（R1 大本墙体、R2 居中、R3 防空覆盖、R4 吹风机、R5 隔间、R6 墙体连贯、R7 仓库贴边、R8 核心防御多样），"
       "输出通过/跳过/证据/建议 + 分数等级；墙数据不完整时墙类规则自动 skip（不误判）\n"
       "- " + c("tools/auto_report.py") + "：一条命令入口 —— " + c("--layout") + " 出报告 / " + c("--dir") + " 批量 / "
       + c("--image") + " 自动标定(带几何合理性校验，拒绝假阳性) + 找同名标注\n"
       "- " + c("tools/enemy_pipeline.py") + " 增加 " + c("rules_eval") + " 输出\n"
       "- 测试：全量 **322 tests OK**（新增 layout_grid 4 项 + layout_rules 3 项）\n")
if "本地路线第一批" not in t:
    open(p, "w", encoding="utf-8", newline="\n").write(t.rstrip() + "\n" + add)
    print("STATUS updated")
