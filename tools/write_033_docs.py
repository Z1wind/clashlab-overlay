# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
def c(s): return BT + s + BT
doc = ("# ClashLab v0.3.3（2026-11-27）\n\n"
       "## 新增\n"
       "- " + c("clashlab/layout_grid.py") + " + " + c("clashlab/layout_rules.py") + "：44×44 布局数据层 + 8 条可解释规则评分\n"
       "- " + c("tools/auto_report.py") + "：一条命令/批量出报告（含自动标定几何校验）\n"
       "- " + c("tools/self_check.py") + "：防守自检 + 推荐打法 + **进攻模拟**（启发式）\n"
       "- " + c("clashlab/battle_sim.py") + " + " + c("tools/sim_attack.py") + "：简化战斗模拟（Dijkstra 寻路 + 防御 DPS 暴露 + 生存率/拆本时间/星级估算）\n"
       "- 标注器 v3：四角吸附、箭线预览（A 键）、保存并出报告（R 键）\n"
       "- ClashKing 免费端点集成：部落成员 TH（cached）、战争（type）、静态数据（max-level）\n"
       "- 面板研究页：F6 识别后显示「部落 TH 分布」后缀\n\n"
       "## 修复\n"
       "- 双击启动可见（无参数 → PANEL，主屏可见）\n"
       "- 繁体中文打包（zhconv 数据）\n"
       "- PANEL 点击切换（去双鼠标通道）、研究/设置页重叠、单实例互斥\n\n"
       "## 说明\n"
       "- 战斗模拟为**启发式估算**（粗粒度兵种表 + 路径暴露），不是游戏真实引擎，仅用于相对比较。\n"
       "- 非官方工具，请自行评估 ToS 风险。\n")
open(os.path.join(BASE, "docs", "RELEASE_v0.3.3.md"), "w", encoding="utf-8", newline="\n").write(doc)
p = os.path.join(BASE, "docs", "STATUS.md")
t = open(p, encoding="utf-8").read()
add = ("\n## 🧮 2026-11-27：战斗模拟（启发式）+ 面板 TH 分布\n\n"
       "- " + c("clashlab/battle_sim.py") + "：44×44 Dijkstra 寻路（墙可破代价4/建筑绕行/大本目标）+ 路径防御 DPS 暴露 × 停留时间 → 生存率/拆本时间/星级估算\n"
       "- " + c("tools/sim_attack.py") + " CLI；" + c("tools/self_check.py") + " 自动带出「进攻模拟」段\n"
       "- 面板研究页对手行追加「 · 部落 TH16×3 TH15×5」后缀（来自 cached 免费端点）\n"
       "- 实测 06 阵：路径 21 格/破墙1/暴露 2038 dps/生存 79%/拆本 6.5s/预估 3 星\n"
       "- 测试：新增 5 项（battle_sim 3 + opponent_th 2），全量 334 OK\n")
if "战斗模拟（启发式）" not in t:
    open(p, "w", encoding="utf-8", newline="\n").write(t.rstrip() + "\n" + add)
    print("docs written")
