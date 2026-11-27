# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
def c(s): return BT + s + BT
doc = "\n".join([
 "# 战场截图 → 报告 工作流",
 "",
 "## 自动抓图（战斗日）",
 "- 计划任务：ClashLabWarCapture2140 / 2150 / 2200（战斗日预热后自动跑）",
 "- 脚本：" + c("tools/war_scout_capture.py") + "（战争地图 → 敌军 → 逐个基地 → 侦察 → 1080p 截图；OCR 状态机 + 断线重连）",
 "- 输出：" + c("out/live/war1080/base_XX_*.png") + "（1920x1080）",
 "",
 "## 候选拼图",
 "- 计划任务：ClashLabWarMontage2152 / 2205",
 "- 脚本：" + c("tools/war_base_montage.py") + "（固定视角标定 1280 手工四角×1.5 → 门控候选 → 4x4 格边距拼图）",
 "- 输出：" + c("out/labels/war/<base>_*.png") + " 与 " + c("<base>_candidates.json"),
 "",
 "## 标注 → 布局 → 报告",
 "1. 看拼图，把每个候选的类型写进 labels JSON：",
 "   " + c('{"quad": [...], "items": [{"image": "...", "tile": [x,y], "size": s, "type": "inferno-tower"}]}') ,
 "2. " + c("python tools/labels_to_layout.py --labels out/labels/real_labels.json --name enemy1") ,
 "3. " + c("python tools/self_check.py --layout out/annotate/enemy1_auto.json --th 15 --report") ,
 "4. 或一步到位：" + c("python tools/scout_to_report.py --image ... --labels ... --name enemy1 --th 15") ,
 "",
 "## 微调类型分类器",
 "- " + c("python tools/finetune_shot_type.py --labels out/labels/real_labels.json --epochs 10") ,
 "- 留出按图片切分；指标同域会偏乐观，仅用于相对比较",
])
open(os.path.join(BASE, "docs", "WAR_CAPTURE_WORKFLOW.md"), "w", encoding="utf-8", newline="\n").write(doc + "\n")
print("workflow doc written")
