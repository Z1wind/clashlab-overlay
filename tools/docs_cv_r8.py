# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
wl = "\n".join([
 "",
 "### 多基留一 CV 烟测（用历史 5 张标注）",
 "- 391 crops / 31 类；留一基 top1 分别为 0.058 / 0.053 / 0.104 / 0.066 / 0.105，mean top1 = 0.077",
 "- 结论：流水线机械上跑通；准确率低是因为历史标注整体偏移（裁剪不含目标建筑），与 r1 的对齐诊断一致",
 "- 等用户用 v0.2.8 新标 10 张（四角目视对齐）后重跑，预期显著提升",
 "- 产物：out/apk_type_report_cv.json、models/apk_type_cls_cv.pt",
 "",
])
open(os.path.join(BASE, "docs", "WORKLOG.md"), "a", encoding="utf-8", newline="\n").write(wl)
print("worklog updated")
