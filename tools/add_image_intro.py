# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
p = os.path.join(BASE, "docs", "CLASHKING_APPLICATION.md")
t = open(p, encoding="utf-8").read()
add = '''
## 附图说明（申请时随截图一起发）

### English

This screenshot shows ClashLab, an open-source (MIT) desktop research tool for Clash of Clans. It runs out-of-process next to the emulator: it captures a war-base screenshot, calibrates the 44x44 grid, scores the enemy layout (defense coverage, weak points), and produces tactical diagrams such as the Queen's Giant Arrow line and deployment suggestions.

In this example, the tool captured a clan-war scouting screen and automatically resolved the opponent from the screenshot (OCR of the in-game name/clan -> player tag -> town hall level and war roster via the API). The JSON output contains the opponent tag, TH level, war size and both clans' member TH levels.

I am applying for CoC API access so this step becomes fully automatic: player tag, TH level and war members are resolved from the API instead of OCR, reducing errors for non-Latin player names. The tool never injects into the game, never reads memory, never automates clicks/attacks, and never performs in-game purchases; API data is used locally for analysis only, with no redistribution or resale.

### 中文

这张图展示的是 ClashLab：一个 MIT 开源的部落冲突阵型分析工具。它以进程外方式贴在模拟器旁：读取战争侦察截图 -> 44x44 网格标定 -> 防守评分（覆盖/弱点）-> 输出战术图（女王穿云箭线路、撒兵建议）。

图中示例是一次真实部落战侦察：工具从截图 OCR 出对手名字/部落，再通过 API 解析出玩家 tag、大本等级和双方参战成员 TH。申请 CoC API 权限是为了把这步自动化：用 API 直接获取 tag/TH/战争成员，减少非拉丁名字的 OCR 错误。工具不注入游戏、不读内存、不自动点击/进攻、不产生任何游戏内消费；数据仅本地分析，不转售不外传。
'''
if "附图说明" not in t:
    t = t.rstrip() + "\n" + add
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("intro doc appended")
