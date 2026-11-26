# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)

doc = '''# UI 语言切换（中文 / English）

给非中文用户用的界面语言开关。

## 切换方式

1. **面板内**：设置页顶部 → 语言 [中文] [English]，点一下立即生效并写入 @config/ui.json@。
2. **启动参数**：@python run_overlay.py --lang en@ / @ClashOverlay.exe --lang en@（auto / zh / en）。
3. **环境变量**：@set CLASHLAB_LANG=en@（优先级最高）。

## 行为

- @zh@：强制中文；
- @en@：强制英文（HUD/PANEL 所有走 @_L(ready, zh, en)@ 的标签立即变英文）；
- @auto@（默认）：沿用旧逻辑——CJK 字体加载成功显示中文，否则显示英文（不叠字、不并排）。

## 已知范围

- 面板标签、按钮、状态行等走 @_L@ 的文案全部双语；
- 部分深层日志/提示仍是中文，会逐步迁移；
- 文档本身已双语（README.md / README.en.md）。
'''
doc = doc.replace("@", BT)
open(os.path.join(BASE, "docs", "I18N.md"), "w", encoding="utf-8", newline="\n").write(doc)

p = os.path.join(BASE, "README.md")
t = open(p, encoding="utf-8").read()
add = "- **中英文界面切换**：设置页 [中文]/[English] 一键切换，或 @--lang en@ / @CLASHLAB_LANG=en@（docs/I18N.md）。\n".replace("@", BT)
if "中英文界面切换" not in t:
    anchor = "## 🗺 路线图"
    t = t.replace(anchor, add + "\n" + anchor, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("README updated")

p2 = os.path.join(BASE, "CHANGELOG.md")
t2 = open(p2, encoding="utf-8").read()
add2 = "- UI 语言切换：设置页 [中文]/[English] + --lang / CLASHLAB_LANG（docs/I18N.md）\n"
if "UI 语言切换" not in t2:
    t2 = t2.replace("## v0.3.0 (unreleased)\n", "## v0.3.0 (unreleased)\n" + add2, 1)
    open(p2, "w", encoding="utf-8", newline="\n").write(t2)
    print("CHANGELOG updated")
