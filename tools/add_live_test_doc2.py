# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)

doc = '''# 实机测试报告（2026-11-26 18:40）

## 环境

- Windows + 雷电模拟器窗口 "雷电模拟器"（1036×595，LDPlayerMainFrame）
- 只读截图：PrintWindow（不点击、不注入、不改游戏）
- 游戏状态：用户正在进攻中（画面右下 49% 摧毁率、剩余 1:24）

## 做了什么

1. @@tools/live_watch.py@@：每 2 秒抓一次游戏窗口 → 裁掉标题栏 → RapidOCR 左上角 → 命中对手名字就调 ClashKing API（fresh=True）。
2. @@python run_overlay.py --seconds 6 --allow-primary@@：覆盖层自检在真实游戏窗口环境下启动，标定数据加载正常（calib tile -> px 输出），6 秒退出、无异常。

## 实机结果（真实日志）

@@@
[ocr] ['防守', 'cHetzz', 'Wrath of Kings']
[api] 命中 → 落盘 out/live/enemy_live.json（18:41:34）
@@@

- OCR 第一版把 UI 文案「防守」当成名字 → **已修**：UI_LABELS 过滤
- 修后解析：name=cHetzz，clan=Wrath of Kings
- API 按名字搜到 **5 个同名 chetzz**：TH11（The event）、TH11（Nova Prime）、TH13（The Revengers）、TH17（[F]allenAngel）、TH13（无部落）
- 部落 Wrath of Kings 有 5+ 个同名部落；公开战争数据均为 warEnded，成员里没有 cHetzz
- 因此返回 **ambiguous=True** + 警告：「同名/部落不匹配：请用玩家标签或点选候选确认」

## 实机测试暴露的问题与修复

| 问题 | 修复 |
|---|---|
| UI 文案「防守/进攻」被当成名字 | UI_LABELS 过滤 |
| 同名玩家多，按名字必错 | 新增 #TAG OCR 提取 + resolve_by_tag（tag 优先，最可靠） |
| 认错人却静默返回 | ambiguous + warning + candidates 列表，面板/CLI 会提示 |

## 本次没做到（诚实说明）

- **没有对敌方基地做布局评分/撒兵线**：API 拿不到敌方阵型图，评分需要建筑位置标注；当前检测器不可用，只能靠人工/APK 标注
- 进攻过程中抓到的「防守」列表只是敌方成员名字，不是侦察界面；侦察界面顶部的 #TAG 才是最可靠输入
- 未做任何游戏内点击/操作（红线）

## 产物

- out/live/enemy_live.json、out/live/enemy_live2.json、out/live/enemy_live_frame.png
- out/logs/live_watch.log、out/logs/selftest_tactics.log
'''
# 句子里的 @@...@@ 用反引号包起来（只替换成对出现的 @@）
while "@@" in doc:
    doc = doc.replace("@@", BT, 2) if doc.count("@@") >= 2 else doc.replace("@@", BT, 1)
open(os.path.join(BASE, "docs", "LIVE_TEST.md"), "w", encoding="utf-8", newline="\n").write(doc)
print("LIVE_TEST.md written")

p = os.path.join(BASE, "README.md")
t = open(p, encoding="utf-8").read()
add = ("- **实机测试**：雷电窗口只读截图 + OCR + API（发现同名歧义并加 #TAG 优先解析），见 "
       + BT + "docs/LIVE_TEST.md" + BT + "。\n")
if "实机测试" not in t:
    anchor = "## 🗺 路线图"
    t = t.replace(anchor, add + "\n" + anchor, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("README updated")
