# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
def c(s): return BT + s + BT
lines = [
 "",
 "## 2026-11-27 自主推进（每小时一批）",
 "",
 "### 一键战报（内置）",
 "- 新增 " + c("clashlab/battle_report.py") + "：规则评分 + 修复建议 + 穿云箭最优落点 + 战斗模拟 + 推荐配比 → 自包含 HTML",
 "- " + c("tools/make_battle_report.py") + " CLI；面板设置页新增「生成战报」按钮（当前阵型直接出 HTML 并打开）",
 "- 06 阵实测：out/reports/th16_06_anti2star_defence17_battle.html 98,453 bytes，A 70.0，预估 3 星",
 "",
 "### 1080p 战场侦察链路",
 "- 新增 " + c("tools/war_scout_capture.py") + "：战争地图 → 敌军 → 逐个基地 → 侦察 → 1080p 截图（OCR 状态机 + 断线重连）",
 "- 实测：准备日连抓 2 个基地成功（out/live/war1080/base_01/02_*.png，1920x1080）",
 "- 已建计划任务 ClashLabWarCapture2140 / 2150：战斗日自动抓图（准备日 21:37 结束）",
 "",
 "### 真实图标补齐",
 "- root-rider / revive 真实图标已补（ClashKingAssets），assets/units_real 39/39 全真实图标",
 "- units.html 重建：1,038,132 bytes（39 图标内嵌），dist/units.html 同步",
 "",
 "### 待办（战斗日后）",
 "- 战斗日抓图 → 战场标定 → 门控候选 → 我逐张标类型 → 微调类型分类器",
]
p = os.path.join(BASE, "docs", "STATUS.md")
t = open(p, encoding="utf-8").read()
if "自主推进" not in t:
    open(p, "w", encoding="utf-8", newline="\n").write(t.rstrip() + "\n" + "\n".join(lines) + "\n")
    print("STATUS updated")
