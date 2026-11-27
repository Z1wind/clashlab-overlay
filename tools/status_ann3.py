# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
def c(s): return BT + s + BT
p = os.path.join(BASE, "docs", "STATUS.md")
t = open(p, encoding="utf-8").read()
add = ("\n## 🎯 2026-11-27：标注器 v3（四角吸附 + 箭线预览）+ 侦察 TH 分布\n\n"
       "- 标注器：点角自动**吸附**附近城墙色像素（±18px）；按 " + c("A") + " 或「箭线预览」后点两点 → 实时显示命中/评分\n"
       "- 服务端 " + c("/arrow") + "：读已保存标注 → " + c("giant_arrow_diagram.match_skewered") + " → hits/summary/score\n"
       "- 侦察流程：" + c("resolve_opponent") + " 现在附带 " + c("clan_th_map") + " / " + c("clan_th_dist") + "（来自免费 cached 端点，无需 token）\n"
       "- E2E 实测：页面 9,346 bytes 含「箭线预览」；save→/arrow 返回 hits=2 summary={air_defense:1,other:1} score=3.0\n"
       "- 测试：全量 329 OK（新增 cached TH 2 项）\n")
if "标注器 v3" not in t:
    open(p, "w", encoding="utf-8", newline="\n").write(t.rstrip() + "\n" + add)
    print("STATUS updated")
