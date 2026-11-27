# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
def c(s): return BT + s + BT
lines = [
 "",
 "## 2026-11-27 战场抓图与标注工具链（准备战斗日）",
 "",
 "- " + c("tools/war_base_montage.py") + "：战场截图 → 固定视角标定（1280 手工四角×1.5）→ 门控候选 → 4x4 格边距拼图",
 "- " + c("tools/finetune_shot_type.py") + "：用「图片+quad+tile+type」标注微调类型分类器（支持每条样本自带 quad），另存模型",
 "- 计划任务：ClashLabWarCapture2140 / 2150（战斗日抓图）、ClashLabWarMontage2152（抓图后自动拼图）",
 "- 说明：Hough 拟合在已知 720p 战图上误差 181px（被 UI 线干扰），故战场标定改用固定视角；实际精度等真实阵验证",
]
p = os.path.join(BASE, "docs", "STATUS.md")
t = open(p, encoding="utf-8").read()
if "战场抓图与标注工具链" not in t:
    open(p, "w", encoding="utf-8", newline="\n").write(t.rstrip() + "\n" + "\n".join(lines) + "\n")
    print("STATUS updated")
