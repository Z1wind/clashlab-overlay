# TH16 / 04 人工标注说明（notes.md，v1）

## 0. 样本完整性（如实降级，最高优先级）

**本样本为不完整样本：村庄菱形上角被裁到画面外，顶部有一片建筑被切掉。** base.png 顶部 y≈0 一线，最外圈两侧墙直接出画、顶角不可见；顶部约 5~8 栋建筑不在画面内（被切掉的上角无法从本图精确计数，只能按可见残部估）。右侧另有站点半透明 "com" 水印压住右上~右中集群。

因此：未录入的 eagle-artillery、scattershot、x-bow、wizard-tower、air-sweeper、hidden-tesla、bomb-tower、multi-archer-tower 以及缺录的第 4 座 air-defense，**疑多在裁切区与右侧水印区，不能据此判断该阵没有这些建筑**；§3 核对表的"图上数到 0/未录入"仅指"本画面内未确认"，不代表实际缺失。

**结论限制：本样本的环容量（meta.ring.cells=595）、core_cover_dps=47064、薄弱扇区、A/B/C 方案只代表画面内部分，不得进入横向对比主表，仅作补充参考。** 本次未重跑 prep/study/marks，链路数字保留原值（见 §6 复现命令），降级仅落文字。

> 标注性质：**纯规则生成、无模型补丁。** 全部建筑人工逐栋判型（layout.json 每栋 `source:"manual"`）；`prep` 不调模型（`out\th16\04\marks.json` `source="rule"`）；`marks --no-llm`（`marks_rule\marks.json`：`model_used=""`、`llm_error=""`、`applied=[]`、`meta.issues=[]`）。

## 1. 定标（quad / Calib）

- `Calib.from_quad(quad)`，quad（上,右,下,左，base.png 原图像素 2622×1206）= `[[1295,10],[2205,617],[1295,1196],[386,604]]`。
- `reproj_error = 0.0`（单应由四角构造，四角重投影恒等，**不代表建筑对位精度**，见 `scripts\th16_04_grid.py` 输出）。
- **包络标定**：左、右顶点取自白色墙掩码最外圈实测（LEFT≈(386,604)、RIGHT≈(2205,617)，`scripts\th16_04_quadfit.py` PCA 拟合）；**顶、底墙尖被图边裁切**（外圈两侧墙在 y≈0 / y≈1206 处出画，顶角/底角不可见），TOP/BOT 取可见包络中点，整村包进 0..43。
- 定标自检：`scripts\th16_04_grid.py` 全图+四角 3x 叠图，黄色网格斜线与同心菱形墙走向吻合，左右顶点落在墙外角（`out\th16_04_probe\g_left/g_right`）；顶/底因裁切有 1~2 格拉伸。
- **未套用其他阵 quad**；未用图片边缘定标；右侧站点半透明水印 "com" 不压建筑主体。

## 2. 精度自评

- **手标误差 ±2~3 格**（1 格≈1 建筑位）：像素取自 2.4~3.2x 分区裁块，十字偏 40~90px（1~2 格），叠加包络拉伸 1 格。大件（TH/monolith/CC）conf 0.70~0.85；火焰塔/炮管类低 conf 0.45~0.65。
- **正射俯视，无透视拉斜**；误差主因是包络拉伸 + 低清渲染下机型混淆，非透视。
- **遮挡/裁切**：顶部外环蓝晶塔群与右上集群被图边裁切+水印压住，只能估或不录；多处圆角/高塔取可见底座中心（monolith、TH 已在 note 注明）。
- 用途限定：相对分布、相对排序、链路走通；不作游戏内逐格对位依据。

## 3. 逐类核对表（图上数到 N，录入 N；基线对照 TH16 约：防空4、地狱塔3、散射炮2、鹰炮1、X弩4、喷火器1、巨石1、法术塔2）

| 类型 | 图上数到 | 录入 | 说明（tile / conf） |
|---|---|---|---|
| town-hall 大本营 | 1 | 1 | (22,28) 红金圆顶 TH16，conf 0.85，可见底座中心取点 |
| monolith 巨石碑 | 1 | 1 | (19,19) 中央黑金 X 形圣碑，conf 0.85；**STATS 未建模**（§4） |
| clan-castle 部落城堡 | 1 | 1 | (32,5) 东侧紫金王冠大厅，conf 0.70；**STATS 未建模**（§4） |
| firespitter 喷火器 | 疑似2 | 2 | (5,30)/(9,40) 红扭树紫座；**STATS 未建模**，低conf 0.45~0.50 估计；基线1 |
| spell-tower 法术塔 | 真蛋糕1 + 玻璃罩紫池疑似4 | 5 | 真蛋糕(26,26) conf0.75；玻璃罩紫池 (1,7)/(4,34)/(39,11)/(36,42) **近似映射 → spell-tower** 0.50~0.55；基线2 |
| inferno-tower 地狱塔 | 火焰红塔估6 | 6 | (16,22)/(22,17)/(26,22) 核心三塔 0.60~0.65；(29,39)/(31,36)/(41,30) 南三环 0.55；均火焰柱红塔估计；基线3 |
| archer-tower 箭塔 | 2 | 2 | (7,1) 北紫甲板、(32,13) 东紫甲板，conf 0.55 估计 |
| cannon 加农炮 | 7（近似映射） | 7 | (8,29)/(15,37)/(27,9)/(34,10)/(38,16)/(42,36)/(43,27)；金齿轮紫心/灰黄重炮 **近似映射 → cannon**，0.50~0.55 |
| air-defense 防空 | 3（画面内） | 3 | (8,26) 三联红炮管、(18,38)/(34,16) 三联红黑条纹火箭，0.55~0.60；**基线4，缺1疑在顶部裁切区/水印区，画面内未确认，不补录** |
| mortar 迫击炮 | 2（近似映射） | 2 | (8,34)/(35,36) 橙色圆碗，**近似映射 → mortar**，conf 0.50 |
| eagle-artillery 鹰火炮 | 0（画面内） | 0 | **疑在顶部裁切区/右侧水印区**，本画面未认出金翼机器人外形，不臆造，**未录入** |
| scattershot 散射炮 | 0（画面内） | 0 | 顶部蓝晶尖塔群被图边裁切+水印，疑在裁切区，未确认，**未录入** |
| x-bow X 连弩 | 0（画面内） | 0 | 画面内灰黄机器多被近似成 cannon，疑在裁切区，未确认连弩外观，**未录入** |
| wizard-tower 法师塔 | 0（画面内） | 0 | 疑在裁切区/水印区，画面内紫色剪影塔未单独认出，**未录入** |
| air-sweeper 吹风机 | 0（画面内） | 0 | 疑在裁切区，画面内未认出风机底座，**未录入** |
| hidden-tesla 特斯拉 | 0（画面内） | 0 | 疑在裁切区，画面内未确认，**未录入** |
| bomb-tower 炸弹塔 | 0（画面内） | 0 | 疑在裁切区，画面内未确认，**未录入** |
| multi-archer-tower 多重箭塔 | 0（画面内） | 0 | 疑在裁切区，画面内未发现红多弩外观，**未录入** |

> `info.json.defense_counts`（dps>0）：monolith1、spell-tower5、inferno-tower6、archer-tower2、firespitter2、cannon7、air-defense3、mortar2、clan-castle1；town-hall 不计入 defense_counts。总量 30 栋。

## 4. 未建模 / 近似映射清单（STATS 无对应，静默兜底 hp1400/dps120/range9）

| type | tile | 图上对象 | 处理方式 |
|---|---|---|---|
| `monolith` | [19,19] | 中央黑金 X 形圣碑 | STATS 未建模，默认兜底，仅作几何与相对排序参考；conf 0.85 |
| `firespitter` | [5,30] | 西红扭树紫座 | STATS 未建模，默认兜底；conf 0.50 估计 |
| `firespitter` | [9,40] | 西南红扭树紫座（疑似第2座） | STATS 未建模，默认兜底；conf 0.45 低conf |
| `clan-castle` | [32,5] | 东紫金王冠大厅 | STATS 未建模，默认兜底，仅作几何参考；conf 0.70 |
| 近似映射 → `spell-tower` | [1,7]/[4,34]/[39,11]/[36,42] | 粉色玻璃罩紫池（非真蛋糕法术塔） | 近似映射：玻璃罩紫池 → spell-tower，0.50~0.55 |
| 近似映射 → `cannon` | [8,29]/[15,37]/[27,9]/[34,10]/[38,16]/[42,36]/[43,27] | 金齿轮紫心机器/灰黄重炮/大管炮（原物或含 Ricochet Cannon、X 弩） | 近似映射：… → cannon，0.50~0.55 |
| 近似映射 → `mortar` | [8,34]/[35,36] | 橙色圆碗 | 近似映射：… → mortar，conf 0.50 |

## 5. 墙体与开口说明（口径约定）

- **本版只录最外圈外墙包络 1 圈**：四边步长 2 连续采样共 **87 点**（外框 gx/gy 0..43，`scripts\th16_04_build_layout.py`）；**内部多圈环形隔断/小房间隔墙一律未录**——`deployment_ring` 用建筑+围墙占位做 9×9 闭运算，内部隔墙铺满会把撒兵环填死，各阵环容量不可比（01 是 366 格，03 铺满隔墙只剩 99 格）。
- 图上可见 ≥3 圈同心菱形墙（外/中/内层层包裹中央核心），真实入兵开口位于各菱形边中点附近（视觉判断），本版包络采样未逐格坐标化开口；顶/底墙尖裁切段由包络补全。
- `meta.ring.cells=595`（`marks_rule\marks.json`，`impl="close_dilate_margin1"`、`ring_fix=true`），由 `clashlab marks --no-llm` 现算，prep 四件套不落此数。

## 6. 复现

```powershell
Set-Location 'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
$env:PYTHONIOENCODING='utf-8'
& 'D:\Python313\python.exe' -m clashlab.api prep --layout bases\th16\04\layout.json --out out\th16\04
& 'D:\Python313\python.exe' -m clashlab study --layout bases\th16\04\layout.json --out out\th16\04\study
& 'D:\Python313\python.exe' -m clashlab marks --layout bases\th16\04\layout.json --out out\th16\04\marks_rule --no-llm
```
