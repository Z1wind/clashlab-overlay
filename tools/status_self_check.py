# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
def c(s): return BT + s + BT
p = os.path.join(BASE, "docs", "STATUS.md")
t = open(p, encoding="utf-8").read()
add = ("\n## 🛡️ 2026-11-27：self_check（防守自检 + 推荐打法 + 穿云箭）\n\n"
       "- " + c("python tools/self_check.py --layout out/annotate/xx_annotated.json --th 16") + "\n"
       "- 输出：规则评分/等级、需要修的规则（含证据与建议）、穿云箭最优 3 条、推荐打法（兵种/法术/步骤/搜索链接）\n"
       "- 实测 06 号阵：70.0 A；wall-confidence=low 时 R1/R5/R6 自动不判定；给出「防空离大本 17 格」critical 建议；推荐 hybrid-miner（矿工21+野猪11+天使4，治疗3+狂暴2）\n"
       "- 价值：标注一次 → 防守修复建议 + 进攻方案同时出；无需 API\n")
if "self_check（防守自检" not in t:
    open(p, "w", encoding="utf-8", newline="\n").write(t.rstrip() + "\n" + add)
    print("STATUS updated")
