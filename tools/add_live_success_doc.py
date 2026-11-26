# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
p = os.path.join(BASE, "docs", "LIVE_TEST.md")
t = open(p, encoding="utf-8").read()
add = '''
## 实机成功案例：真实部落战侦察屏（2026-11-26 21:12）

用户在游戏里打开部落战侦察界面后，ADB 截图 + OCR + API 全链路一次成功：

@@@
[ocr] level='8.' name='SHADOW' clan='babY WaRioR'
[api] player=SHADOW tag=#PLVYQ0G2U TH=17 | clan=baby warior #20R9PL0VU（ambiguous=True）
[war] clan #20R9PL0VU 成员匹配确认：SHADOW #PLVYQ0G2U TH17 mapPosition 8（歧义消除）
@@@

- 截图：@out/live/enemy_scout_live.png@（1280×720，含顶部名字/部落、进攻按钮、战争地图）
- API：@out/live/enemy_scout_live.json@；部落战解析：@out/live/enemy_war_resolved.json@
- 机制说明：OCR 读到的 “8.” 是**地图位次**（不是本等级），TH 以 API/部落战成员数据为准（17）
- 部落战：20v20，warEnded（2026-11-20 ~ 11-21），对方最佳进攻 100%（15.sieepy）

### 下一步（未自动）

敌方建筑**位置**仍需标注（检测器不可用）：用 APK 标注该阵 → 导出 JSON → 跑评分/穿云箭选线；
原始截图已存档，可作为后续检测训练的真实样本。
'''.replace("@@@", BT)
if "实机成功案例" not in t:
    t = t.rstrip() + "\n" + add
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("LIVE_TEST updated")

p2 = os.path.join(BASE, "README.md")
t2 = open(p2, encoding="utf-8").read()
add2 = "- **真实战图实机验证**：部落战侦察屏 OCR+API 一次成功（SHADOW TH17 / #PLVYQ0G2U），见 @docs/LIVE_TEST.md@。\n".replace("@", BT)
if "真实战图实机验证" not in t2:
    anchor = "## 🗺 路线图"
    t2 = t2.replace(anchor, add2 + "\n" + anchor, 1)
    open(p2, "w", encoding="utf-8", newline="\n").write(t2)
    print("README updated")
