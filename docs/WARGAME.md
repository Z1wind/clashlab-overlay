# WARGAME — 赛前兵棋推演引擎

一句话：给定 `layout.json` 和军队构成，用**确定性 tick 推演**跑 N 次 Monte Carlo，输出
**摧毁率分布**、**最佳投放点**和**一局代表性时间线**，用于赛前比较「从哪边下兵、带什么组合」。

- 引擎：`clashlab/wargame.py`（纯 numpy + 标准库）
- CLI：`tools/wargame_cli.py`
- 测试：`tests/test_wargame.py`（7 个用例）
- 本文：输入/输出 schema、算法、参数、复现命令、局限

> 设计参考 NathanNT/clash-battle-engine 的确定性思路（固定 tick、显式目标选择、
> 种子化随机）。**未复制任何上游代码**；开发机无外网（web 检索 HTTP 401），没有逐行
> 核对上游实现，算法以本文件与源码为准。

---

## 1. 快速开始

```powershell
# 200 次 Monte Carlo，输出 JSON 并落盘
D:\Python313\python.exe tools\wargame_cli.py --layout bases/th16/03/layout.json --army '{"giant":15,"wizard":20,"earthquake":4}' --trials 200 --seed 1 --out out/wargame/03_seed1.json

# 测试
D:\Python313\python.exe -m unittest tests.test_wargame -v
```

PowerShell 老版本会把内联 JSON 的双引号吞掉；此时把军队写进文件，用 `--army @army.json`。

Python 内调用：

```python
from clashlab import wargame
res = wargame.run("bases/th16/03/layout.json",
                  {"giant": 15, "wizard": 20, "earthquake": 4},
                  trials=200, seed=1)
one = wargame.simulate_once(layout, army, spawn=(22, 2), seed=0)   # 单场
```

---

## 2. 输入

### 2.1 layout.json

| 字段 | 类型 | 说明 |
|---|---|---|
| `name` | str | 阵型名（只用于回显） |
| `grid` | int | 网格边长，TH16 固定 44（合法格 0–43） |
| `buildings` | list | 建筑数组 |
| `buildings[].type` | str | 建筑类型键，见 `5 数值表 |
| `buildings[].tile` | [x, y] | **中心格**（与仓库既有口径一致） |
| `buildings[].size` | int? | 可选覆盖；默认取数值表 |
| `buildings[].hp/dps/range` | float? | 可选覆盖（测试夹具与手工实验用） |
| `walls` | [[x,y],…] | 单格墙；重复/越界/建筑底下的墙会被剔除 |

占地口径：`footprint 起点 = tile - (size-1)//2`，边长 `size`（`layout_score.footprint_bounds` 同口径）；
偶数尺寸（2×2、4×4）没有唯一中心格，内部按 `x0 + (size-1)/2` 取几何中心。
完全越界的脏数据会被夹到图内（`bases/th16/01` 有一条 `tile=[0,44]`）。

### 2.2 army

```json
{"giant": 15, "wizard": 20, "earthquake": 4}
```

- 兵种（12）：`barbarian, archer, giant, wizard, pekka, hog-rider, valkyrie, golem, witch, bowler, miner, yeti`
- 法术（1）：`earthquake`
- 数量必须是非负整数；未知键直接报错并列出可用键（不静默忽略）。

### 2.3 CLI 参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `--layout` | 必填 | layout.json 路径 |
| `--army` | 必填 | 内联 JSON 或 `@file.json` |
| `--trials` | 200 | Monte Carlo 次数 |
| `--seed` | 1 | 随机种子（只影响投放抖动） |
| `--out` | 无 | 原子写（.tmp → fsync → os.replace） |
| `--tick` | 1.0 | 游戏秒/tick；0.5 更细但耗时约翻倍 |
| `--max-time` | 120 | 单场最长游戏秒 |
| `--wall-hp` | 6000 | 单格墙血量 |
| `--workers` | 0 | 0=自动（trials≥64 时 8 进程，否则串行）；>0 指定进程数 |

---

## 3. 输出 schema

```json
{
  "layout": "bases/th16/03/layout.json",
  "army": {"giant": 15, "wizard": 20, "earthquake": 4},
  "trials": 200,
  "destruction": {"mean": 30.37, "p10": 21.05, "p90": 42.11, "min": 15.79, "max": 44.74},
  "best": {"spawn": [42, 42], "destruction": 41.47},
  "timeline": [{"t": 0.0, "event": "deploy", "detail": "spawn=(42,42) units=35"}, ...],
  "seed": 1,
  "grid": 44,
  "buildings": {"total": 38, "destroyed_mean": 11.54},
  "hp_destroyed": {"mean": 36.34}
}
```

| 字段 | 说明 |
|---|---|
| `destruction` | **按栋数百分比**（CoC 口径：摧毁栋数 / 总栋数 × 100）；p10/p90 用 numpy 线性插值 |
| `hp_destroyed.mean` | 血量加权摧毁率，比栋数口径平滑，用于看“差一点就拆掉” |
| `best.spawn` | 8 个候选投放点里**平均摧毁率最高**的那个（tile 坐标） |
| `best.destruction` | 该投放点的平均摧毁率（不是单局最高值） |
| `timeline` | **最佳投放点下摧毁率最高的一局**的事件流，不是平均局 |
| `buildings.destroyed_mean` | 200 次平均拆掉几栋（便于和“38 栋全拆”对照） |

timeline 事件类型：

| event | 说明 |
|---|---|
| `deploy` | t=0 投放（spawn、单位数） |
| `spell` | t=0 地震（中心、命中栋数、伤害） |
| `building_destroyed` | 建筑血量清空（类型 + tile） |
| `wall_destroyed` | 墙被拆（只保留前 10 条，避免 JSON 膨胀） |
| `defenses_cleared` | 防御建筑全灭的时刻 |
| `end` | 结束原因、摧毁率、存活兵、建筑/墙计数 |

---

## 4. 算法

### 4.1 解析与投放区

1. 建筑按 `tile` + `size` 铺 footprint，写入 `blocked`/`bld_at`；墙写入 `blocked`。
2. 从地图边界做 4 邻域洪泛（墙/建筑都不可通行），取**离边界 ≤2 格**的可通行格作为投放区。
   这样即使阵型没画外圈墙，也不会把兵直接投进建筑堆里。
3. 8 个候选投放点 = 四角 + 四边中点，各自吸附到最近的投放区格（去重）。

### 4.2 部署

每个兵在投放点附近 ±1.6 格抖动（`seed` 驱动），吸附到最近的可站立格；失败则尝试投放点本身。
同格允许叠兵（与游戏里“点两下重叠下兵”一致）。

### 4.3 每 tick 顺序（dt = tick）

1. **选目标**：对每个存活兵计算到所有存活建筑的平方距离。
   - `prefer_defense` 兵种（giant / hog-rider / miner）先只在**防御建筑**里选最近；防御清空后退化为任意建筑。
   - 其余兵种直接选最近建筑。
   - 有效射程 = `兵 range + (size-1)/2`，即近战兵贴到 3×3 建筑边上一格即可开打。
2. **部队输出**：射程内 `dps × dt` 打到目标（`np.bincount` 聚合）。
3. **防御输出**：每个防御选**射程内最近的兵**，`dps × dt` 单目标结算（不建模溅射/连锁/多目标）。
4. **移动**：不在射程内的兵按 8 邻域贪心走一格（`sign(dx), sign(dy)`，允许斜走）。
   - 单 tick 可走 `ceil(最快兵速 × dt)` 个槽，保证改 dt 时「格/秒」语义不变。
   - 下一格是墙 → 打墙；是**挡路的其它建筑** → 打那个建筑；是地图外 → 不动。
   - 被阻挡的兵每 tick 只出手一次（`blocked_done`），避免多槽重复打墙。
5. **结算**：兵/建筑/墙扣血；血量 ≤0 的建筑标记摧毁并释放格子；墙格归零即通行。
6. **终止**：兵全灭 / 建筑全拆 / 到 `max_time`。

### 4.4 地震

开局 `earthquake` 发在 t=0 依次结算，最多 4 发：每发在「所有存活建筑中心」里挑
**预期伤害最大**的位置（命中半径 3.5 格，按边缘距离判定），对半径内每栋建筑造成
**其最大血量的 22%**（不超过当前血量）。不建模施法延迟、弹道、对墙伤害。

### 4.5 Monte Carlo

- 第 `i` 次 trial 用候选点 `i % 8`（分层抽样，保证 8 个点机会均等）。
- 随机性只来自投放抖动：每个 trial 固定 `seed = (seed, i)` → 单次可独立复现。
- 统计：mean / p10 / p90 / min / max（栋数口径）。
- `best`：按 (平均摧毁率, 平均血量摧毁率, -候选序号) 排序取最大。
- `timeline`：在 best 投放点的 trial 里挑摧毁率最高的一局，用同样 seed 复跑并收集事件。

### 4.6 确定性

同样的 `(layout, army, trials, seed, tick, max_time, wall_hp)` → 逐字节相同的输出。
`workers` 只影响墙钟耗时：每个 trial 的 seed 固定，分片后按原顺序拼回，
实测 `parallel_equals_serial = True`。

---

## 5. 数值来源与近似

优先级：`clashlab/assets.py` 的 `stats(name, th=16)` → 内置 `BUILDING_FALLBACK`（同值兜底，assets 不可导入时使用）。

- `STATS` 是 **TH13 基线**（hp/dps/range/size），`TH16_OVERRIDE` 只覆盖
  `monolith / firespitter / ricochet-cannon / clan-castle` 四个。
- 其余建筑（x-bow、cannon、inferno、scattershot…）沿用 TH13 数值：**相对排序可用，
  绝对值不精确**，不要拿它当逐级战力表。
- 墙血量常数 6000/格（TH16 近似，`--wall-hp` 可改）。
- 兵种表为 TH16 近似值；`speed` 以 1 格/tick 实现，表内最快 2.0 格/秒。
- 地震 22%/发、最多 4 发（游戏内约 25%、4 发封顶）。

---

## 6. 性能（实测）

环境：Windows / 16 逻辑核 / Python 3.13.5 / numpy 2.5.5；测量时系统负载约 63%
（雷电 9 模拟器等常驻）。阵型 `bases/th16/03`，军队 15 giant + 20 wizard + 4 earthquake。

| 指标 | 实测 |
|---|---|
| 单场推演（dt=1.0, max_time=120） | **p50 22.4ms / p90 31.9ms / max 35.4ms**（30 次） |
| 200 trials 串行（库默认 `workers=1`） | **4.465s** |
| 200 trials 8 进程（CLI 默认） | **1.143s**（与串行结果逐字节一致） |
| CLI 端到端 200 trials | **1.21s**（引擎计时），进程启动到退出 1.58s |

数字随机器负载波动；机器空闲时更快、被模拟器抢占时会变慢。要稳定低耗时：
`--workers 8`（CLI 默认在 trials≥64 时已自动开 8 进程）。

---

## 7. 复现

```powershell
# 7 个契约测试（含单防御/单部队、墙阻挡、同 seed 确定性、统计范围、摧毁计数、未知兵种）
D:\Python313\python.exe -m unittest tests.test_wargame -v

# 200 次，结果落盘
D:\Python313\python.exe tools\wargame_cli.py --layout bases/th16/03/layout.json --army '{"giant":15,"wizard":20,"earthquake":4}' --trials 200 --seed 1 --out out/wargame/03_seed1.json
```

seed=1 的参考结果（本机）：

```json
{"destruction": {"mean": 30.37, "p10": 21.05, "p90": 42.11, "min": 15.79, "max": 44.74},
 "best": {"spawn": [42, 42], "destruction": 41.47},
 "buildings": {"total": 38, "destroyed_mean": 11.54},
 "hp_destroyed": {"mean": 36.34}}
```

---

## 8. 测试覆盖（tests/test_wargame.py）

1. `test_01_single_defense_kills_unit`：高 dps 防御射程内先打死单兵，建筑不掉血。
2. `test_02_single_unit_destroys_building`：单兵打无防御建筑，血量清空即摧毁（100%）。
3. `test_03_wall_blocks_then_breaks`：墙挡住去路时先啃墙（建筑毫发无损），拆穿后拆建筑；
   无墙对照组更快命中。
4. `test_04_same_seed_is_deterministic`：同 layout/army/trials/seed 两次 `run()` 完全一致。
5. `test_05_mc_stats_and_timeline_valid`：统计满足 `0≤min≤p10≤mean≤p90≤max≤100`；
   best.spawn 在图内；timeline 非空且按时间非降序。
6. `test_06_building_destroyed_count`：2 栋只拆 1 栋 → destroyed=1 / destruction=50%。
7. `test_07_unknown_unit_rejected`：未知兵种报错并列出可用兵种。

---

## 9. 局限（诚实清单）

1. **没有全局寻路**：贪心 8 邻域 + 遇墙拆墙。凹形墙、长墙会让部队原地啃墙，绕路能力弱于真人。
2. **没有空军/溅射/弹道/英雄/宠物/援兵/攻城机器**；除地震外没有狂暴、冰冻、隐身等法术。
3. **不区分对空/对地**：所有防御对所有兵一视同仁（除 dps=0 的建筑）。
4. **防御单目标**：多重箭塔、连弩、巨石碑百分比伤害、地狱塔递增等机制未建模。
5. **数值是近似**：TH13 基线 + TH16 部分覆盖 + 常数墙血，绝对摧毁率不能当胜率；
   只适合「同一阵型下比较不同投放点/组合」的相对排序。
6. **地震是近似**：22%/发、最多 4 发、无递减与弹道。
7. **1 秒离散**：伤害按 tick 结算，微操（提前撤兵、卡弹道、卡攻速）不可表达；
   可用 `--tick 0.5` 换精度（耗时约翻倍）。
8. **投放点只有 8 个**（四角 + 四边中点），不是全边界搜索；best 只是这 8 个里的均值最优。
9. **timeline 不是完整战报**：只记录 best 点下最好的一局，墙事件只留前 10 条。
10. **多进程有调用约定**：`workers>1` 时调用方脚本必须有 `if __name__ == "__main__":`
    保护（Windows spawn 会重新导入主模块，否则会递归重跑）；库默认串行，CLI 自带守卫。
11. **数据质量**：`bases/th16/03` 的墙只录了外圈两环（layout note 自述），内部隔断缺失，
    推演会**低估**拆墙耗时；手工标注的 `conf` 未参与降权。
12. **没有真实战报校准**：未与游戏对局结果做过回归，无法声称胜率预测精度。

---

## 10. 不做的事

- 不连接游戏、不注入进程、不读内存、不自动开打。
- 不做 LLM 决策（那是 `clashlab/overlay/tactics.py` 的职责）。
- 不修改 `bases/`、`config/`、`dist/` 下的任何数据或产物。
- 不替代人工判断：输出是「相对排序 + 可复现的沙盒」，不是真理。
