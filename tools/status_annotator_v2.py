# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
def c(s): return BT + s + BT
p = os.path.join(BASE, "docs", "STATUS.md")
t = open(p, encoding="utf-8").read()
add = ("\n## 🖥️ 2026-11-27：网页标注器 v2（标注→报告一键，工作量最小化）\n\n"
       "- 快捷键：数字 1-9 选类型、W 画墙、U 撤销、C 清空、S 保存、R 保存并出报告\n"
       "- 墙模式：点起点→点终点画墙段（服务端按折线/成对线段自动识别）\n"
       "- 草稿自动存 localStorage，刷新不丢\n"
       "- 新按钮「保存并出报告」：POST " + c("/report") + " → 后端跑 " + c("tools/report_one.py") + " → 页面直接显示评分/箭线/弱点摘要\n"
       "- E2E 实测：页面 HTTP 200（7,096 B）+ save 落盘 + report ok=true（评分 48.7 D、箭线命中 3）\n")
if "网页标注器 v2" not in t:
    open(p, "w", encoding="utf-8", newline="\n").write(t.rstrip() + "\n" + add)
    print("STATUS updated")
