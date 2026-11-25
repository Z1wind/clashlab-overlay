# TH16 / 05 人工标注说明（notes.md，首版 v1）

## 版本说明（v1）

- **v1**：21 栋建筑 / 136 个墙体格点（外墙包络口径，见 §5）。
- 来源：`bases\th16\05\source.json` —— clashofclans-layouts.com `/plans/th_16/war_139.html`，TH16 CWL Anti-3star War Base #139，`role=["anti-3star","war-cwl"]`，原图 2622×1206 / 840797 字节，不规则多格分区战争阵。
- 判型方法：2.0~3.5x 分区裁块 + 高倍特写 + `assets\coc\buildings` 最高等级模板联系表（`scripts\th16_05_refsheet.py`）比对；全部 `source:"manual"`。
- **样本完整性核对（独立看图，未照抄 source.json 标注）**：逐边带复核——顶边 y0~170 全宽（含远左上 600~1050、远右上 1900~2350）、底边 y1120~1206、左边 x330~430、右边 x2260~2360：四角均在画面内，四周为岩石/岩浆留白，**无建筑被画面边缘切掉一半**，草地未触及任何画面边缘，判定为**完整样本**。注意：`source.json` 的 `completeness="顶部裁切"` / `crop_note` 与图面不符（图上顶部无贴边半切建筑），此处以本图独立核对为准；该差异不影响坐标录入。

> 标注性质：**纯规则生成、无模型补丁。** `api snap` 在本图不可用（沿用 01/03 结论，离线链路不调模型）；全部建筑人工逐栋判型；`prep` 不调模型（`out\th16\05\marks.json` `source="rule"`）；`marks --no-llm`（`marks_rule\marks.json`：`model_used=""`、`llm_error=""`、`applied=[]`、`meta.issues=[]`、`coord_audit.issues=[]`）。

## 1. 定标（quad / Calib）

- `clashlab.geo.Calib.from_quad(quad)`，quad（上,右,下,左）= `[[1326,31],[2307,500],[1391,1164],[290,610]]`（base.png 原图像素，2622×1206）。
- 四角来源：草地颜色掩码（HSV H18-38 / S55-175 / V105-215）最大并集凸包，`approxPolyDP` 取菱形上尖 (1326,31)、右极 (2307,661)、下尖 (1391,1164)、左极 (387,651)，再按包络相切把右/左角微调至 (2307,500)/(290,610) 使西缘防空簇与东北缘箭塔落在 0..43 内；**未套用 01/02/03 的 quad**（`scripts\th16_05_quad.py` / `th16_05_hullpoly.py` 独立重算）。
- `reproj_error = 0.0`（单应由四角构造，四角重投影恒等，**不代表建筑对位精度**）。
- 包络标定：四角取草地边界外留空，整村包进 0..43，内部网格相对墙面有拉伸，是 ±2~3 格误差的主因。

## 2. 精度自评

- **手标误差 ±2~3 格**（1 格≈1 建筑位）：像素取自 2.0~3.5x 裁块坐标网格，单点偏 1 格内；叠加包络单应拉伸 1 格。大件（TH/鹰炮/CC/monolith）conf 0.75~0.90；判型存疑/贴边条目 conf 0.55~0.65。
- **正射俯视，无透视拉斜**：站点原图为完整村庄俯视，镜头正射；误差来自包络拉伸而非透视。
- **遮挡**：右侧站点半透明淡水印（"com"）压右中~右上，不遮挡建筑主体；高密度分区内部分型只能低 conf 估计，相关条目见 §3 备注。
- **边缘条目**：西缘 3 座防空被包络夹到 gx=0 列（raw gx -1.08~0.05，钳到 0），北缘箭塔 [17,0]、南缘箭塔 [22,43]、南缘火喷 [15,43] 同理，属包络外偏，非位移。
- 用途限定：相对分布、相对排序、链路走通；不作游戏内逐格对位依据。

## 3. 逐类核对表（图上数到 N，录入 N；缺失低于基线必须说明）

| 类型 | 图上数到 | 录入 | 说明（tile / conf） |
|---|---|---|---|
| town-hall 大本营 | 1 | 1 | [28,25]，红金圆顶大厅，conf 0.90 |
| eagle-artillery 鹰火炮 | 1 | 1 | [17,24]，金翼橙青机械，conf 0.75 |
| scattershot 散射炮 | 疑似 1 | 1 | [36,34]，右下棕旋绿芯炮台，conf 0.55 估计；**基线 2 座，第 2 座与履带机器/储物混淆，未确认不补录** |
| inferno-tower 地狱塔 | 确认 2 | 2 | [18,26]、[18,20]，红柱火焰塔，均 conf 0.55 估计；**基线 3 座，其余红柱与防空/火喷外观近似难分，未确认不补录** |
| x-bow X 连弩 | 0 | 0 | 图上未见蓝色弩台，**未发现，未录入** |
| cannon 加农炮 | 疑似 1 | 1 | [25,35]，大红金管黑底，conf 0.60 估计 |
| archer-tower 箭塔 | 4 | 4 | [1,3] conf 0.65、[17,0] conf 0.65 贴北缘、[6,37] conf 0.65、[22,43] conf 0.60 贴南缘；紫色木台外观 |
| multi-archer-tower 多重箭塔 | 0 | 0 | 未发现红多弩/青菱外观，**未录入** |
| wizard-tower 法师塔 | 0 | 0 | 灰裂紫座塔与祭坛/罐簇混淆，未确认，**未录入** |
| air-defense 防空 | 4 | 4 | [0,23]/[0,19]/[0,16]/[4,26]，红柱蓝晶塔，均 conf 0.55，**近似映射（§4）；4/4 达基线** |
| mortar 迫击炮 | 疑似 1 | 1 | [38,39]，红口圆臼，conf 0.55 估计 |
| air-sweeper 吹风机 | 1 | 1 | [25,4]，金台蓝涡，conf 0.65；dps=0 不计入 info.defense_counts |
| hidden-tesla 特斯拉 | 0 | 0 | 不可见防御，图上无证据，**未录入** |
| bomb-tower 炸弹塔 | 0 | 0 | 未确认，**未录入** |
| spell-tower 法术塔 | 0 | 0 | 粉色蛋糕/紫药外观未确认，**未录入**；**基线 2 座，缺 2，未确认不补录** |
| monolith 圣碑 | 1 | 1 | [38,28]，深灰金修长高塔，conf 0.75；未建模（§4） |
| firespitter 喷火器 | 疑似 3 | 3 | [2,15] conf 0.60、[3,27] conf 0.55、[15,43] conf 0.55 贴南缘；红扭树紫座，**基线 1 座，多出为估计/可能混型，未建模（§4）** |
| clan-castle 部落城堡 | 1 | 1 | [41,30]，紫顶金冠大厅，conf 0.80；未建模（§4） |

> TH16 战争阵一般基线：防空 4 / 地狱塔 3 / 散射炮 2 / 鹰炮 1 / X 弩 4 / 喷火器 1 / 巨石 1 / 法术塔 2。本图密度高 + 右侧水印 + TH16 皮肤与 TH13 模板有差异，**地狱塔 2/3、散射炮 1/2、法术塔 0/2、X 弩 0/4 均低于基线，原因是未确认而非图上不存在；禁止留空编造，全部低 conf 估计或不补录**。
> `info.json.defense_counts` 只统计 dps>0（town-hall dps=0、air-sweeper dps=0 不计）；21 栋中 10 类入 defense_counts（eagle/scatter/inferno×2/AD×4/archer×4/cannon/mortar/monolith/firespitter×3/CC）。

## 4. 未建模 / 近似映射建筑清单（STATS 15 类外，未知 type 静默按 hp1400/dps120/range9 兜底）

| type | tile | 图上中文名 | 处理方式 |
|---|---|---|---|
| `monolith` | [38,28] | 深灰金修长高塔（圣碑） | STATS 未建模，默认兜底 hp1400/dps120/range9，仅作几何与相对排序参考；conf 0.75 |
| `firespitter` | [2,15] | 红扭树紫座（火喷外观） | STATS 未建模，默认兜底；conf 0.60 |
| `firespitter` | [3,27] | 红扭树紫座（火喷外观） | STATS 未建模，默认兜底；conf 0.55 估计 |
| `firespitter` | [15,43] | 红扭树紫座（火喷外观） | STATS 未建模，默认兜底；conf 0.55 估计；贴南缘 |
| `clan-castle` | [41,30] | 紫顶金冠大厅 | STATS 未建模，默认兜底，仅作几何与相对排序参考；conf 0.80 |
| `air-defense` ×4 | [0,23]/[0,19]/[0,16]/[4,26] | 红柱蓝晶塔 | **近似映射：红柱蓝晶塔 → air-defense**（TH16 皮肤与 TH13 模板有差异，外观判型置信低，conf 0.55） |

## 5. 墙体与开口说明（外墙包络口径）

- walls 共 **136 格**：**只录外墙包络 1 圈**——外框四边（tile 空间 gx=0/44、gy=0/44）步长 2 连续采样 ∪ 奶油色墙掩膜在草地凸包内侧 55px 带内实测命中的外墙格（`scripts\th16_05_walls.py` / `th16_05_wallgen.py`）。
- **内部隔断 / 小房间隔墙未录（口径约定）**：本阵为不规则多格分区，内部横竖隔墙密布；若全部录入，`deployment_ring` 的 9×9 闭运算会把撒兵环填死，环容量不可与 01（366）横比，故内部隔墙一律不录。
- 分段：外墙包络按 4 段描述——北段（gy≈0，gx 0→44）、东段（gx≈44，gy 0→44）、南段（gy≈44，gx 44→0）、西段（gx≈0，gy 44→0）；真实外墙上的入兵缺口视觉上位于各边中段附近，本版未逐格标注开口坐标（包络近似，不逐块描墙）。
- 可撒格数：`meta.ring.cells=865`（`marks_rule\marks.json`，`impl="close_dilate_margin1"`、`ring_fix=true`）；外墙包络口径下内部隔墙不占位，环容量显著大于 03 密集隔墙样本（99），与 01（366）口径相同、不跨样本比绝对值。

## 6. 复现

```powershell
Set-Location 'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
$env:PYTHONIOENCODING='utf-8'
& 'D:\Python313\python.exe' -m clashlab.api prep --layout bases\th16\05\layout.json --out out\th16\05
& 'D:\Python313\python.exe' -m clashlab study --layout bases\th16\05\layout.json --out out\th16\05\study
& 'D:\Python313\python.exe' -m clashlab marks --layout bases\th16\05\layout.json --out out\th16\05\marks_rule --no-llm
```
