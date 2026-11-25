# TH16 / 01 人工标注说明（notes.md，第二版 v2）

## 版本变更（v1 → v2）

- **v1**：30 栋建筑 / 71 个墙体抽样点（每 4 格稀疏抽样）。
- **v2**：31 栋建筑 / 141 个墙体点（三层连续方框，步长 2，≤2 格连续采样）。
- 改了什么、为什么：
  1. **补录 1 栋**：第二遍 9 个 3x 分区 + 紧图复核，在 (32,12) 确认 1 座红塔黄色火焰柱的 **inferno-tower**（藏在红色祭坛后），note 标"第二遍复核补录"。
  2. **墙体重写**：v1 的 71 点对整圈墙过稀，`deployment_ring` 闭运算前会在环上留空洞、可撒格数虚高；v2 改三层连续方框（外框 0..43、内框 10..33、核心框 20..23）沿四边步长 2 连续采样。
  3. 其余建筑坐标与判型沿用 v1（含低 conf 估计条目），未改类型。
- 重跑产物：prep 四件套、study（study.png/study.json）、marks(--no-llm) 全部按 v2 重新落盘；可撒格数 `meta.ring.cells` **v1=290 → v2=366**（原因见 §5）。

> 标注性质：**纯规则生成、无模型补丁。** `api snap` 在本图 0 候选不可用；全部建筑人工逐栋判型；`prep` 不调模型（`source` 恒 `rule`）；`marks --no-llm`（`model_used=""`、`llm_error=""`、`applied=[]`、`meta.issues=[]`）。

## 1. 定标（quad / Calib）

- `Calib.from_quad(quad)`，quad（上,右,下,左）= `[[1180,90],[2150,480],[1180,1180],[500,480]]`（base.png 原图像素）。
- `reproj_error = 0.0`（单应由四角构造，四角重投影恒等，**不代表建筑对位精度**）。
- 包络标定：四角取最外墙体外留空处，整村包进 0..43，内部网格相对墙面有拉伸，是 ±2~3 格误差的主因。

## 2. 精度自评

- **手标误差 ±2~3 格**（1 格≈1 建筑位）：初测像素来自 3.5x 裁块联系表，十字标偏 50~100px（1~2 格），叠加包络拉伸 1 格。大件（TH/鹰火炮/monolith）conf 0.80~0.90；贴边/遮挡条目 conf 0.55~0.65。
- **正射俯视，基本无透视拉斜**；仅包络 quad 右/下留空略多，致右、下贴边条目外偏（夹到 43），非图像透视。
- **遮挡**：右侧站点半透明水印 "com" 压住右上~右中，顶部气球/骷髅 CC 装饰压顶部集群，相关条目只能估计。
- 用途限定：相对分布、相对排序、链路走通；不作游戏内逐格对位依据。

## 3. 逐类核对表（图上数到 N，录入 N；第二遍复核后）

| 类型 | 图上数到 | 录入 | 说明 |
|---|---|---|---|
| town-hall 大本营 | 1 | 1 | (18,14)，conf 0.90 |
| eagle-artillery 鹰火炮 | 1 | 1 | (43,40)，conf 0.85 贴下边界 |
| scattershot 散射炮 | 图上仅确认 1 座红白旋塔 | 1 | (10,6)，conf 0.60；其余红台与 X 弩/祭坛混淆，不补录 |
| inferno-tower 地狱塔 | 1（第二遍补录） | 1 | (32,12)，火焰柱红塔，conf 0.60，第二遍复核补录 |
| x-bow X 连弩 | 4 | 4 | (34,6)/(10,30)/(26,34)/(40,20) |
| cannon 加农炮 | 3 | 3 | (38,16) 近似映射 0.55、(34,40)、(40,28) |
| archer-tower 箭塔 | 0 | 0 | 第二遍 9 区+紧图复核：疑似小塔均为 mortar/cannon 簇，**未发现**，不录入 |
| multi-archer-tower 多重箭塔 | 0 | 0 | 未发现红多弩外观，**未录入** |
| wizard-tower 法师塔 | 4 | 4 | (24,40)/(30,44)/(43,20)/(43,32) |
| air-defense 防空 | 3 | 3 | (22,8)/(30,36)/(40,24) |
| mortar 迫击炮 | 2 | 2 | (30,40)/(43,24) |
| air-sweeper 吹风机 | 4 | 4 | (36,38)/(40,36)/(38,40)/(43,36)；dps=0 不计入 info.defense_counts |
| hidden-tesla 特斯拉 | 2 | 2 | (26,2)/(43,16)，均估计 |
| bomb-tower 炸弹塔 | 1 | 1 | (20,44) 贴下边界 |
| spell-tower 法术塔 | 1 | 1 | (26,22) |
| monolith | 1 | 1 | (32,28)，未建模（§4） |
| firespitter 喷火器 | 0 | 0 | 第二遍复核未见双喷嘴喷火装置；简化俯视下与祭坛/罐簇无法区分，**未录入** |
| clan-castle 部落城堡 | 1 | 1 | (8,2)，未建模（§4） |
| ricochet-cannon | 1 | 1 | (12,38)，未建模（§4） |

> info.json.defense_counts 只统计 dps>0（air-sweeper×4、town-hall×1 不计）；v2 计数 26 条 dps>0，总量 31 栋。

## 4. 未建模 / 近似映射建筑清单（STATS 无对应，静默兜底 hp1400/dps120/range9）

| type | tile | 图上中文名 | 处理方式 |
|---|---|---|---|
| `clan-castle` | [8,2] | 顶部紫色大厅 | STATS 未建模，默认兜底，仅作几何与相对排序参考；conf 0.60 |
| `monolith` | [32,28] | 黑金方尖碑 | STATS 未建模，默认兜底；conf 0.80 |
| `ricochet-cannon` | [12,38] | 左下红灰重炮（疑似 Ricochet Cannon） | STATS 未建模，默认兜底；conf 0.55（保留真实英文名，未改 cannon 串） |
| `cannon`(38,16) | [38,16] | 右上红灰重炮 | 近似映射：cannon（原物或为 Ricochet Cannon），conf 0.55 |

## 5. 墙体与开口说明

- v2 walls 共 **141 点**：三层轴对齐方框，四边步长 2 连续采样（外框 gx/gy 0..43；中框 10..33；核心框 20..23）。
- 这是**连续多边形近似**，未逐块描真实墙体；真实墙为同心菱形+分格，开口（入兵缺口）视觉上位于内圈各边中点附近，本版未逐格标注开口坐标。
- 可撒格数对比：v1 稀疏墙 71 点 → `meta.ring.cells=290`；v2 连续墙 141 点 → `meta.ring.cells=366`。两版口径相同（`close_dilate_margin1`），差异仅来自墙体样本密度，本报告不对升降机制作归因，两版绝对值不跨版比较。

## 6. 复现

```powershell
Set-Location 'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
$env:PYTHONIOENCODING='utf-8'
& 'D:\Python313\python.exe' -m clashlab.api prep --layout bases\th16\01\layout.json --out out\th16\01
& 'D:\Python313\python.exe' -m clashlab study --layout bases\th16\01\layout.json --out out\th16\01\study
& 'D:\Python313\python.exe' -m clashlab marks --layout bases\th16\01\layout.json --out out\th16\01\marks_rule --no-llm
```
