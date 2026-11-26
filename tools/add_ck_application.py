# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
doc = '''# ClashKing / Hog Rider 开发者申请：可直接粘贴的英文模板

Discord 弹窗里的问题是：

> What you plan to do with the CoC API? Provide brief examples of the features your tool will have.
> （至少 80 字符）

## 推荐填写（直接复制）

I am building ClashLab, an open-source (MIT) desktop research tool for Clash of Clans base analysis. It reads a screenshot of an enemy war base, calibrates the 44x44 grid, scores the layout, recommends tactics and simulates deployments in 2D.

I would like CoC API access to automatically resolve a player's town hall level, clan and current war members from player/clan tags, so the tool can fill in troop/hero levels and opponent TH without manual input.

The tool is strictly read-only and out-of-process: it never injects into the game, never reads game memory, never automates attacks or clicks, and never spends gems or performs any in-game action. API data is only used locally for analysis; it is not resold or redistributed. I will respect rate limits, follow your terms and Supercell's Fan Content Policy, and credit ClashKing in the project.

## 可选：Other Languages 一栏

Chinese (Simplified and Traditional) and English interface.

## 注意

- 不要填 Discord 密码或任何账号凭据（表单也提示了）。
- 不要写「自动打资源/自动进攻」这类会被拒的用途；本工具确实也不做这些。
- 长度已超过 80 字符要求。
'''
doc = doc.replace("@@@", BT)
open(os.path.join(BASE, "docs", "CLASHKING_APPLICATION.md"), "w", encoding="utf-8", newline="\n").write(doc)
print("written")
