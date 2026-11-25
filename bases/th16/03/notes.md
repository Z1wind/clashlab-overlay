# TH16 / 03 人工标注说明（notes.md，v2）

## 版本变更（v1 → v2）

- **v1（已废弃，仅留档 scratch/layout_v1_backup.json）**：14 栋 / 778 墙格 / `meta.ring.cells=99`。
- **v2（本版）**：38 栋 / 152 墙格 / `meta.ring.cells=227`。
- 改了什么、为什么：
  1. **防御补录**：v1 只录 14 栋，x-bow / cannon / mortar / air-sweeper / archer-tower / scattershot 大面积缺失，薄弱扇区与覆盖 DPS 不成立；v2 用 3×3 分区 3 倍放大图逐区（上/下/左/右/四角/中心）补录，新增 24 条（含 v1 保留条目像素复核）。
  2. **墙体重录（口径统一，横向对比用）**：v1 的 778 格是颜色掩码全量采样，含内部隔断/小房间隔墙，`deployment_ring` 9×9 闭运算把城内填死，环只剩 99 格；v2 只录**最外圈包络线**（tile 空间曼哈顿 d∈[20,23]，贴包络内侧一圈），内部隔断全部未录（口径约定同 01 号阵），环恢复到 227 格。
- 判型方法：9 个 3×3 分区裁块（`scripts\th16_03_gridfine.py`，50px 坐标网格）+ 候选定点 4x 特写联系表（`scripts\th16_03_zoom.py` / `th16_03_zoom2.py`）+ `assets\coc\buildings` 最高等级模板（`scripts\th16_03_tpl16.py`）比对；全部 `source:"manual"`。

> 标注性质：**纯规则生成、无模型补丁。** `api prep` 不调模型（`out\th16\03\marks.json` `source="rule"`）；`marks --no-llm`（`marks_rule\marks.json`：`model_used=""`、`llm_error=""`、`applied=[]`、`meta.issues=[]`、`coord_audit.issues=[]`）。

## 1. 定标（quad / Calib）

- `clashlab.geo.Calib.from_quad(quad)`，quad（上,右,下,左）= `[[1288,12],[2314,569],[1281,1193],[282,562]]`（base.png 原图像素，2622×1206），**未套用 01 的 quad**。
- 四角由草地颜色掩码最大连通域四极取得，去贴边带；`reproj_error = 0.0`（单应由四角构造，四角重投影恒等，**不代表建筑对位精度**）。
- 包络标定：四角取草地边界留空、未贴墙尖，整村包进 0..43，内部有拉伸，是 ±2~3 格误差主因。

## 2. 精度自评

- **手标误差 ±2~3 格**（1 格≈1 建筑位）：包络标定留空 + 单应拉伸；补录条目像素取自分区特写，粗略偏移 50~100px，落格后由 debug_overlay 逐象限核对，落空的 4 条（CAN(1,10)、MOR(7,39)、CAN(36,30)、XB(36,31) 重复）已剔除。
- **正射俯视，无透视拉斜**：站点原图为完整村庄俯视；误差来自包络拉伸而非透视。
- **遮挡**：右侧站点半透明淡水印压右上~右中；高密度建筑群与 TH16 皮肤差异使部分类型无法确认，相关条目只给低 conf（0.45~0.60）估计或不录入（逐条见 §3）。
- **debug_overlay.png**：`out\th16\03\debug_overlay.png`，base.png 缩小后叠每栋方格+类型缩写+外圈墙点；四象限放大核对，大件落本体，疑似条目偏差 ±1~2 格，无整格错位。
- 用途限定：相对分布、相对排序、链路走通；不作游戏内逐格对位依据。

## 3. 逐类核对表（图上数到 N，录入 N；缺失低于基线必须说明）

| 类型 | 图上数到 | 录入 | 说明（tile / conf） |
|---|---|---|---|
| town-hall 大本营 | 1 | 1 | (17,28)，红金圆顶，conf 0.90 |
| eagle-artillery 鹰火炮 | 1 | 1 | (16,16)，金翼平台，conf 0.85 |
| monolith 圣碑 | 1 | 1 | (7,8)，黑金圣碑，conf 0.85；未建模（§4） |
| clan-castle 部落城堡 | 1 | 1 | (2,36)，紫蓝王冠大厅，conf 0.80；未建模（§4） |
| spell-tower 法术塔 | 1 | 1 | (16,38)，粉色蛋糕蜡烛，conf 0.80；**基线 2 座，第 2 座与资源建筑混淆未确认，不补录** |
| firespitter 喷火器 | 2 | 2 | (8,33) conf 0.65；(36,18) conf 0.55 红扭树紫座；未建模（§4） |
| air-defense 防空 | 3 | 3 | (15,21)/(18,21)/(21,19) 红柱蓝晶塔，conf 0.55，近似映射；**基线 4 座，缺 1 座被簇群遮挡未确认** |
| inferno-tower 地狱塔 | 2 | 2 | (25,9) conf 0.70 v1 保留；(12,17) conf 0.55 红柱黄束近似映射；**基线 3 座，其余红柱与防空外观近似难分** |
| scattershot 散射炮 | 4 | 4 | (15,7) v1 conf 0.55；(12,30) conf 0.55、(4,12) conf 0.50、(32,16) conf 0.50 红三管；**基线 2 座，多出 2 座为外观近似估计，可能与 x-bow/cannon 混判，conf 0.50** |
| x-bow X 连弩 | 9 | 9 | (0,11)/(0,15)/(19,0)/(29,2)/(33,3)/(38,5)/(43,17)/(43,21)/(36,34)，金黑轨炮，conf 0.55，**近似映射：金黑轨炮 → x-bow**；**基线 4 座，数量为目视估计，密度高+皮肤差异可能偏高，未逐个锁定模板** |
| cannon 加农炮 | 3 | 3 | (23,39)/(35,26) 紫管 conf 0.55；(19,4) 灰红大口径 conf 0.50；近似映射 |
| mortar 迫击炮 | 2 | 2 | (22,26) 灰竖管 conf 0.50；(40,5) 红口圆柱 conf 0.45 疑似；估计 |
| air-sweeper 吹风机 | 1 | 1 | (23,0) 蓝红曲柄风袋 conf 0.55，近似映射；**基线 4 座，其余被水印/簇群遮挡未确认** |
| archer-tower 箭塔 | 6 | 6 | (33,22) v1 紫台 conf 0.60；(16,0) conf 0.60；(34,34)/(34,23)/(33,39)/(39,40) conf 0.55 |
| bomb-tower 炸弹塔 | 1 | 1 | (23,43) 黑金杯状 conf 0.45 贴下边界估计 |
| wizard-tower 法师塔 | 0 | 0 | **全区分区未见深绿尖塔外观（模板：深绿灰尖塔紫座），未发现，未录入**；簇群内红灰塔身与模板不符，不强行归类 |
| multi-archer-tower 多重箭塔 | 0 | 0 | **未见米色开口环台外观，未发现，未录入** |
| hidden-tesla 特斯拉 | 0 | 0 | 不可见防御，图上无证据，未录入 |

> TH16 战争阵一般基线：防空 4 / 地狱塔 3 / 散射炮 2 / 鹰炮 1 / X 弩 4 / 喷火器 1 / 巨石 1 / 法术塔 2。本图高密度 + 右侧水印 + TH16 皮肤与 TH13 模板有差异；**低于基线处均为未确认而非图上不存在，禁止编造**；x-bow/scattershot 高于基线为目视估计偏高，已标低 conf。

## 4. 未建模 / 近似映射建筑清单（STATS 15 类外，未知 type 静默按 hp1400/dps120/range9 兜底）

| type | tile | 图上中文名 | 处理方式 |
|---|---|---|---|
| `monolith` | [7,8] | 黑金圣碑 | STATS 未建模，默认兜底 hp1400/dps120/range9，仅作几何与相对排序参考；conf 0.85 |
| `firespitter` | [8,33] | 红扭树紫座 | STATS 未建模，默认兜底；conf 0.65 |
| `firespitter` | [36,18] | 右侧红扭树紫座 | STATS 未建模，默认兜底；conf 0.55 |
| `clan-castle` | [2,36] | 紫蓝王冠大厅 | STATS 未建模，默认兜底，仅作几何与相对排序参考；conf 0.80 |
| `air-defense` ×3 | [15,21]/[18,21]/[21,19] | 红柱蓝晶塔 | **近似映射：红柱蓝晶塔 → air-defense**（TH16 皮肤与 TH13 模板有差异，conf 0.55） |
| `x-bow` ×9 | 见 §3 | 金黑轨炮 | **近似映射：金黑轨炮 → x-bow**（TH16 皮肤，conf 0.55） |
| `cannon` ×3 | 见 §3 | 紫管/灰红炮 | **近似映射：紫管炮 → cannon**（conf 0.50~0.55） |
| `inferno-tower` [12,17] | [12,17] | 红柱黄束 | **近似映射 → inferno-tower**（conf 0.55） |
| `air-sweeper` [23,0] | [23,0] | 蓝红曲柄风袋 | **近似映射 → air-sweeper**（conf 0.55） |

## 5. 墙体与开口说明（v2 口径）

- walls 共 **152 格**：取 v1 颜色掩码墙格，仅保留 tile 空间距中心(22,22) 曼哈顿距离 d∈[20,23] 的最外圈包络线（贴包络内侧一圈），**d<20 的内部隔断/小房间隔墙全部未录（口径约定，同 01 号阵外围口径）**；d>23 为包络外噪声，剔除。
- 结构：方格网格，最外一圈为菱形包络墙；第二圈以内隔断本版按口径不录。
- 开口：外圈掩码采样未逐格核对入兵缺口；目视未见外圈大开口，开口坐标本版不标注。
- 可撒格数：v1=99（778 格全量墙，内部隔墙填死）→ **v2=227**（152 格外圈，`meta.ring.cells`，`marks_rule\marks.json`，`impl="close_dilate_margin1"`）。

## 6. 复现

```powershell
Set-Location 'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
$env:PYTHONIOENCODING='utf-8'
& 'D:\Python313\python.exe' -m clashlab.api prep --layout bases\th16\03\layout.json --out out\th16\03
& 'D:\Python313\python.exe' -m clashlab study --layout bases\th16\03\layout.json --out out\th16\03\study
& 'D:\Python313\python.exe' -m clashlab marks --layout bases\th16\03\layout.json --out out\th16\03\marks_rule --no-llm
```
