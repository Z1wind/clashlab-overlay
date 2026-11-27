# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
def c(s): return BT + s + BT
doc = ("# ClashLab v0.3.4（2026-11-27）\n\n"
       "## 新增\n"
       "- **真实兵种/法术/英雄图标**：37 张 ClashKing/Statscell 素材（MIT 仓库，Supercell 美术版权归原方），"
       "缺 2 个（root-rider / revive）自动回退自制图标\n"
       "- " + c("out/units.html") + " 升级为真实图标（990,740 bytes，39 张图标内嵌 base64）\n"
       "- 面板设置页新增「打开兵种/法术表」按钮（一键打开内置页面）\n"
       "- 构建时自动把 " + c("units.html") + " 复制到 dist/，与 exe 一起分发\n\n"
       "## 说明\n"
       "- 图标素材来自 ClashKingInc/ClashKingAssets 与 Statscell/clash-assets（开源仓库），游戏美术版权归 Supercell；"
       "仅用于本地个人工具，不再分发美术素材本身。\n")
open(os.path.join(BASE, "docs", "RELEASE_v0.3.4.md"), "w", encoding="utf-8", newline="\n").write(doc)
print("release notes written")
