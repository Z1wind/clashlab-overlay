# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
with open(os.path.join(BASE, "docs", "WORKLOG.md"), "a", encoding="utf-8", newline="\n") as f:
    f.write("\n".join([
        "",
        "## 方案3：混合 + 独特外形贴图二次校验（2026-11-28 19:25）",
        "- 在混合方案上加「13 种独特外形建筑的贴图 NCC 校验」，阈值与 t3 一起网格搜索",
        "- 结果：P51.4 / R63.8 / F1 .564 / type 80.0%（差于混合 P62.3/R71.0/F1 .658）",
        "- t3=0（即不启用贴图校验）在 8 折中被选 4 次；fold5 出现退化（pred=0），拉低均值",
        "- 结论：贴图二次校验对混合方案没有稳定增益，保持 v1.5 混合方案（已交付）",
        "- 脚本：tools/train_hybrid_tpl_cv.py；报告：out/hybrid_tpl_report.json",
        "",
    ]))
print("worklog updated")
