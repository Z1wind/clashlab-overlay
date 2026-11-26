# 大本营支持矩阵（TH1–TH19）

> 面向「全大本营可用」这一目标，本文说明：**每档数据到底精确到什么程度、识别模型实际覆盖到哪一档、哪些数字是外推的**。
> 数据实现：`clashlab/th_data.py`；契约测试：`tests/test_th_data.py`（15 项）。
> 最近核对：2026-11-26（TH16 数值未回归、全量单测 221 项 OK）。

## 一句话结论

- **数据层**已覆盖 TH1–TH19：每档都能查到网格、大本营尺寸、解锁建筑列表、关键防御 hp/dps/range，并带 `source` / `confidence`。
- **识别模型仍只覆盖 TH16 的 19 类建筑**（27px 档 CNN）。TH16 以外的布局没有对应标注数据，识别结果**不可直接采信**；TH17–TH19 的新建筑（多齿轮塔、复仇塔、超级法师塔、尖刺塔、爆竹塔等）**完全没有识别标签**。
- **数值可信度分两层**：几何/解锁/最高等级是 reviewed 精确值；hp/dps 只有 TH13 基线、TH16 四类 wiki 值，TH17–TH19 是**明确标注的低置信外推**（本机无外网，拿不到官方逐级数值）。

## 数据来源

| # | 来源 | 覆盖内容 | 可信度 | 说明 |
|---|------|----------|--------|------|
| 1 | 本地 vendored ruleset `out/overlay/_p3a/upstream/clash-of-clans-base-validator-main/rulesets/home-2026-11-17.json` | 网格 44×44、每栋建筑尺寸、每档解锁列表、每档最高等级（TH1–19） | **高（reviewed）** | `review_status: reviewed`、`verified_on: 2026-11-17`、`asset_build: 19.32.5`；fact_review 记录已检查 2128 个 per-TH 等级值与 112 个 footprint 维度。子集已内联进 `th_data.SIZE / UNLOCKED / LEVELS`，运行时不依赖 out/ 副本 |
| 2 | `clashlab/assets.py` 的 `STATS` | TH13 的 hp/dps/range/level | 中（近似） | 其自带注释即写明「只用于相对排序，不追求逐级精确」 |
| 3 | `clashlab/assets.py` 的 `TH16_OVERRIDE` | TH16 的 monolith / ricochet-cannon / clan-castle / firespitter | 高（firespitter 为低） | 前三个为 wiki 口径；firespitter 是 TH17 解锁，登记值本身标 `confidence=low` |
| 4 | 内部外推 | TH17–TH19 的 hp/dps/range | **低** | 以 TH16 快照记录等级为基准，用 reviewed 的该档最高等级求 Δ：`hp × 1.07^Δ`、`dps × 1.08^Δ`，range 不变；每条都带 `note` 写明公式与 Δ |
| 5 | `assets.DEFAULT_FALLBACK` | 任何数据源都没有的建筑 | 低 | hp1400 / dps120 / range9，`unknown=True` |

## 每档状态

状态口径：**已精确** = 有 reviewed 或 wiki 直接来源；**近似** = 回退到更低档或有标注的外推；**未验证** = 没有该档数值，只能通用兜底。

| TH | 几何 / 解锁 / 等级 | hp / dps / range | 综合状态 | 说明 |
|----|--------------------|------------------|----------|------|
| TH1–TH12 | 已精确 | 未验证 | **未验证** | 没有该档数值表，`stats()` 返回通用兜底（hp1400/dps120/range9），只保证不越界 |
| TH13 | 已精确 | 近似 | **近似** | `assets.STATS` TH13 基线（36 栋解锁） |
| TH14 | 已精确 | 近似 | **近似** | 无独立表，回退 TH13（偏低） |
| TH15 | 已精确 | 近似 | **近似** | 无独立表，回退 TH13（偏低） |
| TH16 | 已精确（尺寸沿用 STATS 口径） | 近似（4 类精确 + 15 类沿用 TH13） | **近似** | `TH16_OVERRIDE` 的 monolith/ricochet-cannon/clan-castle 为 wiki 值；其余建筑仍是 TH13 数值（现有行为，未改） |
| TH17 | 已精确 | 近似（外推，low） | **近似** | 新增 firespitter、multi-gear-tower；41+ 栋解锁 |
| TH18 | 已精确 | 近似（外推，low） | **近似** | 新增 revenge-tower、super-wizard-tower |
| TH19 | 已精确 | 近似（外推，low） | **近似** | 新增 spiky-tower、firecracker-tower、guardian-shrine；47 栋解锁 |

> 没有任何一档的 hp/dps 达到「全量精确」。TH16 是唯一有专门数值表的档位，但只有 4 类建筑是 wiki 值。

## 关键防御数值（hp / dps / range / 等级）

`*` = 该格来自更低档或通用兜底（`approx=True`）。

| 建筑 | TH13 | TH16 | TH17 | TH18 | TH19 |
|------|------|------|------|------|------|
| cannon | 1200/118/9 L16 | 1200/118/9 L16 | 1683/173/9 L21 | 1683/173/9 L21 | 1683/173/9 L21 |
| air-defense | 1500/330/10 L10 | 1500/330/10 L10 | 2104/485/10 L15 | 2251/524/10 L16 | 2409/566/10 L17 |
| x-bow | 3000/200/11 L6 | 3000/200/11 L6 | 4502/317/11 L12 | 4817/343/11 L13 | 5155/370/11 L14 |
| eagle-artillery | 4000/350/11 L3 | 4000/350/11 L3 | 5243/476/11 L7 | 5243/476/11 L7 | 5243/476/11 L7 |
| scattershot | 3000/290/11 L2 | 3000/290/11 L2 | 3932/395/11 L6 | 4208/426/11 L7 | 4208/426/11 L7 |
| monolith | 兜底* | 5353/193/11 L3 | 5728/208/11 L4 | 6129/225/11 L5 | 6129/225/11 L5 |
| firespitter | 兜底* | 4500/410/16 L1 | 4815/443/16 L2 | 5152/478/16 L3 | 5152/478/16 L3 |
| ricochet-cannon | 兜底* | 5700/390/9 L2 | 6099/421/9 L3 | 6526/455/9 L4 | 6983/491/9 L5 |
| multi-archer-tower | 1600/140/10 L2 | 1600/140/10 L2 | 1712/151/10 L3 | 1832/163/10 L4 | 1960/176/10 L5 |
| clan-castle | 兜底* | 5600/0/0 L12 | 5992/0/0 L13 | 6411/0/0 L14 | 6860/0/0 L15 |
| spiky-tower | — | — | — | — | 兜底*（尺寸 3、等级 2 来自 reviewed 表） |

> 这张表是「相对排序可用、绝对数值别当真」的典型：cannon 的 TH16 值仍是 TH13 基线（1200/118），TH17 起才按等级差外推到 Lv21。

## 识别模型覆盖（关键限制）

- 模型只认 **TH16 的 19 类**（`tools/cnn_own.py:79` 的 `DEF` 去掉 `wall`）：
  `air-defense, air-sweeper, archer-tower, bomb-tower, cannon, eagle-artillery, firespitter, hidden-tesla, inferno-tower, monolith, mortar, multi-archer-tower, scattershot, spell-tower, town-hall, wizard-tower, x-bow, clan-castle, ricochet-cannon`。
- `layout.json` 的类型白名单是 18 种（`clashlab/baselink.py:111` 的 `SYNTHETIC_BUILDING_TYPES`）+ 城墙 = 19 类；与模型口径一致。
- **TH16 以外的档位**：没有按档采集/标注的数据，识别与布局导入只能「先标注再用」；`bases/` 目前只有 `bases/th16/01–06` 六阵。
- **TH17–TH19 新建筑**没有识别标签：`multi-gear-tower`、`revenge-tower`、`super-wizard-tower`、`spiky-tower`、`firecracker-tower`、`guardian-shrine`、`crafting-station`。要用它们必须先补标注。

## 用法

```python
from clashlab import assets, th_data

th_data.supported_town_halls()      # [1, 2, ..., 19]
th_data.grid_size(17)               # 44（所有档一致）
th_data.town_hall_meta(17)          # grid / town_hall_size / unlocked / status / confidence / source / note
st = th_data.stats("monolith", 19)  # hp/dps/range/size/level + th/approx/approx_from/source/confidence/unknown
st["approx"]                        # False = 命中该档表；True = 回退（看 approx_from）
assets.stats("cannon", 16)          # 委托 th_data；数值与旧实现逐项一致
assets.stats("cannon")              # th=None 仍走旧 STATS 语义（无 approx 键）
```

`approx` 语义：

| 情况 | `approx` | `approx_from` | 例子 |
|------|-----------|----------------|------|
| 命中该档数值表 | False | None | `stats("monolith", 19)` |
| 回退到不高于该档的最近表 | True | 该表档位 | `stats("x-bow", 15)` → 13 |
| 该建筑无任何 hp/dps 记录 | True | None | `stats("spiky-tower", 19)`、`stats("ghost-tower", 16)` |

## 已知限制（不要当成 bug）

1. **本机无外网**（2026-11-26 实测：web_search 401、web_fetch `fetch failed`），TH17–19 的 hp/dps 无法与官方逐级数据核对，只能用等级差外推并标 `confidence=low`。
2. 外推系数（hp 7%/级、dps 8%/级）是经验值，未与真实战报校准；跨档比较请只看相对排序。
3. **TH16 的 15 类非覆盖建筑仍是 TH13 数值**——这是「TH16 不回归」的硬约束，改它会动 `bases/th16` 的评分/推演结果。
4. **尺寸口径差异（刻意保留）**：TH≤16 的 size 沿用 `assets.STATS`（例如 eagle-artillery=3），TH17–19 的 size 用 reviewed 表（eagle-artillery=4）。前者是历史口径，后者才是真实 4×4；切换前需评估 `plan_render` / `giant_arrow_diagram` 的渲染影响。
5. 网格 44×44 是 reviewed board 约定，ruleset 自己仍把「live 编辑器独立测量」列为未解决项。
6. TH1–TH12 没有 hp/dps 数据，`stats()` 返回通用兜底；做低本推演前应先补表。

## 复跑

```powershell
D:\Python313\python.exe -m unittest tests.test_th_data -v     # 15 项契约测试
D:\Python313\python.exe -m unittest discover -s tests          # 全量（221 项）
```
