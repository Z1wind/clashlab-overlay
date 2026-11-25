# TH16 / 06 人工标注说明（notes.md，v1）

> 标注性质：**纯规则生成、无模型补丁。** `prep` 不调模型（`out\th16\06\marks.json` `source="rule"`）；`marks --no-llm`（`marks_rule\marks.json`：`model_used=""`、`llm_error=""`、`applied=[]`、`meta.issues=[]`）。全部建筑人工逐栋判型（layout.json 每栋 `source:"manual"`），未用模型补位。

## 1. 定标（quad / Calib）

- `Calib.from_quad(quad)`，quad（上,右,下,左）= `[[1278,27],[2087,668],[1306,1215],[454,618]]`（base.png 原图像素）。
- 定标方法：金色描边+奶油白双掩膜抓不到左/暗面墙，改用 RANSAC 分边带拟合四条外墙外线（斜率约束 0.55~0.85），取四交点为 quad；`clashlab.geo.Calib.from_quad(quad)`，`reproj_error=0.0`（单由四角构造，四角重投影恒等，**不代表建筑对位精度**）。
- 网格叠图确认：四条拟合外线贴外墙，整村包进 0..43，未用图片边缘、未套用其他阵 quad；右侧站点淡水印未纳入定标。

## 2. 精度自评

- **手标误差 ±2~3 格**（1 格≈1 建筑位）：像素中心由 3×3 25px 标尺 atlas 扫全图记录，程序 `px_to_tile` 换算四舍五入夹 0..43；叠加包络拉伸约 1 格。
- **正射俯视，基本无透视拉斜**；误差主因是包络标定下内部网格相对墙面的拉伸，非图像透视。
- **遮挡**：右侧站点半透明水印 "com" 压住右上~右中，该区域条目只能估计；贴边/被装饰压住的条目 conf 0.50~0.55。
- 用途限定：相对分布、相对排序、链路走通；不作游戏内逐格对位依据。

## 3. 逐类核对表（图上数到 N，录入 N；v1 复核后）

| 类型 | TH16 基线 | 图上数到 | 录入 | 说明（坐标 / conf / 缺口理由） |
|---|---|---|---|---|
| town-hall 大本营 | 1 | 1 | 1 | (19,18)，中央红金大本营，conf 0.90 |
| eagle-artillery 鹰火炮 | 1 | 0 | 0 | 全图复核（黑甲机械群、右上水印压区）未见金翼炮大型炮座，**未发现，不补录** |
| scattershot 散射炮 | 2 | 2 | 2 | (7,3) conf 0.50 棕金机器人近似；(43,42) conf 0.70 三管金簇近似 |
| inferno-tower 地狱塔 | 3 | 4 | 4 | (7,5)/(7,37)/(35,4)/(39,39)，金环红焰塔 conf 0.80；超基线 1 座：其中一座或为 x-bow/祭坛，外观未确证 |
| x-bow X 连弩 | 4 | 0 | 0 | 灰蓝弩台（xbow L13）未见；6 座黑甲机械外观与 x-bow 不符，标 ricochet-cannon 未确证，**不升格** |
| cannon 加农炮 | 6 | 6 | 6 | (7,17)/(4,2)/(3,40)/(13,36)/(41,0)/(26,0)，红管金座近似映射，conf 0.55~0.60 |
| archer-tower 箭塔 | 6 | 7 | 7 | 蓝晶紫亭 7 座：(0,17)/(0,20)/(15,23)/(17,39)/(43,12)/(21,40)/(36,19)，conf 0.55；超基线 1：外观近似 archer L21 紫立方，未确证，也可能含 spell-tower |
| multi-archer-tower 多重箭塔 | — | 0 | 0 | 米色多层平台未见，**未录入** |
| wizard-tower 法师塔 | 5 | 14 | 14 | 红橙/绿顶炉塔批量近似映射 wizard-tower，conf 0.55~0.60；**大幅超基线**：本截图红炉塔外观与 wiz17 绿岩塔不符，真实类型可能为 cannon/x-bow/祭坛，未逐座确证，仅作几何与相对排序 |
| air-defense 防空 | 4 | 1 | 1 | (22,0) 红塔近似 conf 0.55；**缺 3 座**：蓝金叠立方（ad16）全图未定位，其余疑似点复核为紫亭/红塔，不补录 |
| mortar 迫击炮 | 2 | 1 | 1 | (38,1) 红橙迫击炮近似 conf 0.55；**缺 1 座**：第二座蓝圆盘未定位 |
| air-sweeper 吹风机 | 2 | 0 | 0 | 红黑风扇炮（sweep7）未见，**未录入** |
| hidden-tesla 特斯拉 | 2 | 3 | 3 | (17,0)/(24,19)/(16,19)，小黑炮估计 conf 0.50；超基线 1，未确证 |
| bomb-tower 炸弹塔 | 2 | 1 | 1 | (8,29) 黑黄方塔 conf 0.75；**缺 1 座**：第二座白蓝圆柱未定位 |
| spell-tower 法术塔 | 2 | 1 | 1 | (15,14) 粉穹蛋糕状近似 conf 0.50；**缺 1 座**：第二座未定位 |
| monolith | 1 | 1 | 1 | (30,29) 黑金方尖碑 conf 0.70，未建模（§4） |
| firespitter 喷火器 | 1 | 0 | 0 | 蓝金四足兽（firespit3）未见，**未录入** |
| clan-castle 部落城堡 | 1 | 0 | 0 | 初版误标 4 座紫色大厅：复核 3 座为紫条纹资源桶（金/圣水储存）已剔除，第 4 座紫亭归 archer-tower；真实 CC 未确认，**未录入** |
| ricochet-cannon | TH16 新建筑 | 6 | 6 | (0,2)/(4,0)/(24,39)/(37,42)/(42,36)/(38,24)，黑甲履带机 conf 0.50，未建模（§4） |

> info.json.defense_counts 只统计 dps>0：archer-tower×7、wizard-tower×14、cannon×6、ricochet-cannon×6、inferno-tower×4、scattershot×2、hidden-tesla×3、air-defense×1、bomb-tower×1、spell-tower×1、mortar×1、monolith×1；town-hall×1 不计。录入总量 48 栋。
> 本阵最大不确定项：wizard-tower×14 明显超基线（红炉塔批量近似），air-defense 仅 1 座（蓝金叠立方未定位）；两者均已低 conf 标注并在此表说明，未用"皮肤差异/认不出"糊过。

## 4. 未建模 / 近似映射建筑清单（STATS 无对应，静默兜底 hp1400/dps120/range9）

| type | tile | 图上外观 | 处理方式 |
|---|---|---|---|
| `monolith` | [30,29] | 黑金方尖碑 | STATS 未建模，按默认 hp1400/dps120/range9 兜底，仅作几何与相对排序；conf 0.70 |
| `ricochet-cannon` ×6 | [0,2]/[4,0]/[24,39]/[37,42]/[42,36]/[38,24] | 黑甲履带机 | STATS 未建模，默认兜底；也可能是 x-bow/eagle 深色皮肤，未确证，conf 0.50（保留真实英文名，未改 cannon 串） |

近似映射（用 STATS 原串，note 已注明）：
- `wizard-tower` 14 座：红橙/绿顶炉塔 → wizard-tower（L17 红橙火焰塔外观最接近），conf 0.55~0.60；
- `archer-tower` 7 座：蓝晶紫亭 → archer-tower（L21 紫立方外观近似），conf 0.55；
- `air-defense` [22,0]、`cannon`×6、`scattershot`×2、`hidden-tesla`×3、`spell-tower`×1、`mortar`×1：均为低 conf 近似映射，note 已逐栋注明。

## 5. 墙体与开口说明

- walls 共 **116 点**：只录**外墙包络**（quad 四条外墙外线，沿边步长≈1.5 格连续采样，≤2 格间隔），内部隔断/小房间隔墙**未录**（团队口径）。
- 外墙为菱形转置方框，本版沿四条拟合外线连续采样；未逐格标注真实墙体块，未逐格标注入兵缺口坐标（菱形四边视觉连续，开口位置未单独定位）。

## 6. 复现

```powershell
Set-Location 'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
$env:PYTHONIOENCODING='utf-8'
& 'D:\Python313\python.exe' -m clashlab.api prep --layout bases\th16\06\layout.json --out out\th16\06
& 'D:\Python313\python.exe' -m clashlab study --layout bases\th16\06\layout.json --out out\th16\06\study
& 'D:\Python313\python.exe' -m clashlab marks --layout bases\th16\06\layout.json --out out\th16\06\marks_rule --no-llm
```
