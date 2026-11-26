# 实机测试报告（2026-11-26 18:40）

## 环境

- Windows + 雷电模拟器窗口 "雷电模拟器"（1036×595，LDPlayerMainFrame）
- 只读截图：PrintWindow（不点击、不注入、不改游戏）
- 游戏状态：用户正在进攻中（画面右下 49% 摧毁率、剩余 1:24）

## 做了什么

1. `tools/live_watch.py`：每 2 秒抓一次游戏窗口 → 裁掉标题栏 → RapidOCR 左上角 → 命中对手名字就调 ClashKing API（fresh=True）。
2. `python run_overlay.py --seconds 6 --allow-primary`：覆盖层自检在真实游戏窗口环境下启动，标定数据加载正常（calib tile -> px 输出），6 秒退出、无异常。

## 实机结果（真实日志）

`@
[ocr] ['防守', 'cHetzz', 'Wrath of Kings']
[api] 命中 → 落盘 out/live/enemy_live.json（18:41:34）
`@

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

## 实机成功案例：真实部落战侦察屏（2026-11-26 21:12）

用户在游戏里打开部落战侦察界面后，ADB 截图 + OCR + API 全链路一次成功：

`
[ocr] level='8.' name='SHADOW' clan='babY WaRioR'
[api] player=SHADOW tag=#PLVYQ0G2U TH=17 | clan=baby warior #20R9PL0VU（ambiguous=True）
[war] clan #20R9PL0VU 成员匹配确认：SHADOW #PLVYQ0G2U TH17 mapPosition 8（歧义消除）
`

- 截图：@out/live/enemy_scout_live.png@（1280×720，含顶部名字/部落、进攻按钮、战争地图）
- API：@out/live/enemy_scout_live.json@；部落战解析：@out/live/enemy_war_resolved.json@
- 机制说明：OCR 读到的 “8.” 是**地图位次**（不是本等级），TH 以 API/部落战成员数据为准（17）
- 部落战：20v20，warEnded（2026-11-20 ~ 11-21），对方最佳进攻 100%（15.sieepy）

### 下一步（未自动）

敌方建筑**位置**仍需标注（检测器不可用）：用 APK 标注该阵 → 导出 JSON → 跑评分/穿云箭选线；
原始截图已存档，可作为后续检测训练的真实样本。

## 战图收集（2026-11-26 21:2x，用户逐个点开敌方基地）

| 文件 | OCR 名字 | 部落 | tag | TH |
|---|---|---|---|---|
| map_01.json | SuVRO | Sumon 2 | #92PPC2RVQ | 8 |
| scout_01_6a402f3c30.json | SHADOW | babY WaRioR | #PLVYQ0G2U | 17 |
| war_01.json | SUVRO Sumon 2 | babY WaRioR | #LR8GVY892 | 16 |

- 采集器 @tools/war_map_collect3.py@：按 API tag 去重、8 分钟窗口；
- 修复：玩家名折行（SUVRO / Sumon 2）曾被当成两个字段，现在 >=3 行时最后一行才是部落，中间并入名字；新增测试。
