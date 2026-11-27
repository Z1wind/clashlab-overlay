# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
def c(s): return BT + s + BT
p = os.path.join(BASE, "docs", "STATUS.md")
t = open(p, encoding="utf-8").read()
add = ("\n## 🧩 2026-11-27：面板进攻模拟 + 兵种/法术可视化（带图标）\n\n"
       "- 面板研究页新增「模拟：X侧 路径N 破墙N 生存N% N★」行（默认 hybrid-miner 配比，按布局指纹缓存）\n"
       "- 新增 " + c("clashlab/units.py") + "：21 兵种 / 13 法术 / 5 英雄数据（dps/hp/住房/半径/持续/用途/颜色/字形）\n"
       "- 新增 " + c("tools/build_units_page.py") + "：生成 39 个 PNG 图标（assets/units/）+ " + c("out/units.html") + "（88,352 bytes，图标内嵌 base64）\n"
       "- 标注器服务新增 " + c("/units") + " 路由（浏览器直接看兵种/法术/英雄卡片 + 知识库推荐配比）\n"
       "- 测试：新增 units 3 + battle_sim_line 3，全量 340 OK\n")
if "兵种/法术可视化" not in t:
    open(p, "w", encoding="utf-8", newline="\n").write(t.rstrip() + "\n" + add)
    print("STATUS updated")
