# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
p = os.path.join(BASE, "docs", "STATUS.md")
t = open(p, encoding="utf-8").read()
add = ("## 💾 备份（GitHub Release）\n\n"
       "- **backup-2026-11-26**（prerelease）：https://github.com/Z1wind/clashlab-overlay/releases/tag/backup-2026-11-26\n"
       "- 资产：@@ClashOverlay.exe@@（121,346,737 B，md5 CEE1FBBB…）+ @@clashlab_annotated_20261126.zip@@（11,674,555 B，md5 1476B595…；含 6 阵标注 JSON、真实战图、批量压测报告）\n"
       "- 源码：仓库 main 分支 + tag 的自动源码 zip\n"
       "- 校验：下载 zip 实测 HTTP 200 / Content-Length 11,674,555 / md5 与本地一致\n").replace("@@", BT)
if "backup-2026-11-26" not in t:
    open(p, "w", encoding="utf-8", newline="\n").write(t.rstrip() + "\n\n" + add)
    print("STATUS backup section added")

p2 = os.path.join(BASE, "README.md")
t2 = open(p2, encoding="utf-8").read()
add2 = ("- 下载 / 备份：[Releases](https://github.com/Z1wind/clashlab-overlay/releases)"
        "（最新 " + BT + "backup-2026-11-26" + BT + "：exe + 标注数据 zip）。\n")
if "backup-2026-11-26" not in t2:
    anchor = "## 🗺 路线图"
    t2 = t2.replace(anchor, add2 + "\n" + anchor, 1)
    open(p2, "w", encoding="utf-8", newline="\n").write(t2)
    print("README updated")
