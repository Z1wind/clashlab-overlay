# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)

# ---------- 英文润色 ----------
p = os.path.join(BASE, "clashlab", "overlay", "pages.py")
t = open(p, encoding="utf-8").read()
PO = {
 '"local rule engine, offline"': '"Local rule engine, offline"',
 '"LLM online plan generation"': '"LLM plan generation (online)"',
 '"research"': '"Research"', '"layout"': '"Layout"', '"collect"': '"Capture"', '"setting"': '"Settings"',
 '"ON"': '"Live"', '"dry"': '"Dry run"',
 '"Refresh"': '"Refresh intel"',
 '"no layout loaded: press auto-capture"': '"No layout loaded - press Auto-capture"',
 '"Auto capture"': '"Auto-capture"',
 '"highlighted on HUD"': '"Highlighted on HUD (others dimmed)"',
 '"nothing to mark"': '"Nothing to annotate"',
 '"Goal"': '"Goal"', '"Army"': '"Army"', '"Equip"': '"Equipment"',
 '"AI failed; local analysis active"': '"AI failed - switched to local analysis"',
 '"failed: "': '"Generation failed: "',
 '"Generate"': '"Generate plan"',
 '"press Generate for a 3-part plan."': '"Press Generate plan for a three-part plan."',
 '"Phases"': '"Phases"', '"Threats"': '"Threats"', '"Filter"': '"Filter"', '"All"': '"All"',
 '"Exit add"': '"Finish boxes"', '"Add box"': '"Add box mode"',
 '"Hide"': '"Hide"', '"Show"': '"Show"', '"Del"': '"Delete"',
 '"Freeze layout"': '"Lock layout"',
 '"Run study"': '"Run research"',
 '"background; auto-reload"': '"Runs in background; auto-reloads"',
 '"no base: grid/diamond reference; click to add-box"': '"No base image: grid/diamond is a reference - click to add boxes"',
 '"Start"': '"Start capture"', '"Stop"': '"Stop capture"',
 '"clicks.log tail"': '"Recent clicks (last 20)"',
 '"Hotkeys"': '"Hotkeys"',
 '"defaults avoid LD hotkeys (F8/F9/F11)"': '"Defaults avoid LDPlayer hotkeys (F8/F9/F11)"',
 '"Reset"': '"Reset to defaults"',
 '"ESC cancels capture; use [Clear] to unbind"': '"ESC cancels capture; use Clear to unbind"',
 '"Panel position"': '"Panel position"',
 '"Recalibrate"': '"Recalibrate"',
 '"show view-changed badge on HUD"': '"Show the view-may-have-changed badge on HUD"',
 '"Fit offset (runtime saves config)"': '"Fit offset (saved by the runtime)"',
 '"Exit"': '"Exit"',
 '"(close window also exits)"': '"(closing the window also exits)"',
 '"(applies instantly)"': '"(applies instantly)"',
}
for a, b in PO.items():
    t = t.replace(a, b)
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("english polished")

# ---------- 文档 ----------
p2 = os.path.join(BASE, "docs", "I18N.md")
t2 = open(p2, encoding="utf-8").read()
if "繁體" not in t2:
    t2 = t2.replace("- @en@：强制英文", "- @zh-hant@：繁體中文（設置頁按鈕「繁體」，由 zhconv 簡繁轉換）；\n- @en@：强制英文")
    t2 = t2.replace("2. **启动参数**：@python run_overlay.py --lang en@ / @ClashOverlay.exe --lang en@（auto / zh / en）。",
                    "2. **启动参数**：@python run_overlay.py --lang en@ / @ClashOverlay.exe --lang en@（auto / zh / zh-hant / en）。")
    open(p2, "w", encoding="utf-8", newline="\n").write(t2)
    print("I18N doc updated")

p3 = os.path.join(BASE, "docs", "TACTICS.md")
t3 = open(p3, encoding="utf-8").read()
if "英雄落点" not in t3:
    add3 = '''
## 5. 英雄落点与穿云箭方向（谨慎测试）

- 英雄部署后优先攻击**最近建筑的中心**；穿云箭方向 = 英雄位置 → 最近建筑中心 的连线。
- 因此落点偏移 **0.1–0.5 格**就可能换目标，整条箭线命中的建筑随之改变。
- 本项目新增 @tools/arrow_placement_cli.py@：输入落点，输出最近目标、箭线角度、命中列表，并在落点周围 ±0.5 格采样做**敏感性测试**（stable / flips）。
- 实机结论：先在离线阵型上跑敏感性，stable=False 的落点禁止用于实战；进游戏再用截图核对目标建筑。
'''.replace("@", BT)
    t3 = t3.rstrip() + "\n" + add3
    open(p3, "w", encoding="utf-8", newline="\n").write(t3)
    print("TACTICS doc updated")

p4 = os.path.join(BASE, "README.md")
t4 = open(p4, encoding="utf-8").read()
add4 = ("- **英雄落点→穿云箭方向**：按「最近建筑中心」推箭线，并做 ±0.5 格落点敏感性测试（stable/flips）；"
        + BT + "tools/arrow_placement_cli.py" + BT + "。\n"
        "- **三语界面**：设置页 [中文] [繁體] [English]，或 " + BT + "--lang zh-hant" + BT + "。\n")
if "英雄落点" not in t4:
    anchor = "## 🗺 路线图"
    t4 = t4.replace(anchor, add4 + "\n" + anchor, 1)
    open(p4, "w", encoding="utf-8", newline="\n").write(t4)
    print("README updated")

p5 = os.path.join(BASE, "CHANGELOG.md")
t5 = open(p5, encoding="utf-8").read()
add5 = ("- 界面三语：简体/繁體/English；英文文案润色（标签/按钮/提示统一）。\n"
        "- 英雄落点→穿云箭方向：最近建筑中心决定箭线 + 落点敏感性测试（arrow_placement_cli）。\n")
if "三语" not in t5:
    t5 = t5.replace("## v0.3.0 (unreleased)\n", "## v0.3.0 (unreleased)\n" + add5, 1)
    open(p5, "w", encoding="utf-8", newline="\n").write(t5)
    print("CHANGELOG updated")
