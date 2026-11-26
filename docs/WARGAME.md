# 赛前兵棋推演（wargame）

设计参考 [NathanNT/clash-battle-engine](https://github.com/NathanNT/clash-battle-engine)（MIT，C++20，确定性 battle simulator）：固定时间步、显式目标选择、可复现随机种。这里是纯 Python 简化版，只用于「方案 A vs 方案 B」的相对比较，不追求逐帧还原游戏数值。

## 输入

- `layout.json`：`{grid, buildings:[{type,tile}], walls:[[x,y]]}`（缺省 hp/dps/range 取 `clashlab/assets.py` 的 STATS）
- `army`：`{兵种: 数量}`，兵种：barbarian / archer / giant / wizard / wall-breaker / balloon / dragon / golem / pekka / hog-rider / miner / bowler / valkyrie / witch / yeti；法术：earthquake
- 投放点：`spawn=(x, y)` tile 坐标；`run()` 会自动在三条边各取一个候选点并按 best 排序

## 接口

```python
from clashlab import wargame
one = wargame.simulate_once('bases/th16/03/layout.json', {'giant': 5, 'wizard': 8}, spawn=(22, 2), seed=0)
mc  = wargame.run('bases/th16/03/layout.json', {'giant': 8, 'wizard': 12, 'earthquake': 2}, trials=200, seed=1)
```

### simulate_once 输出

`{time, tick, units_alive, units_total, buildings_destroyed, buildings_total, destruction, hp_destroyed, walls:{total, destroyed, hp_remaining}, events:[{t,event,...}], timeline}`

- `destruction`：摧毁建筑数 / 建筑总数（%）；
- `hp_destroyed`：被打掉的建筑血量（tile 口径汇总）；
- `events`：`start / building_destroyed / unit_died / wall_destroyed / end`，按时间递增；
- `timeline`：按秒采样的快照。

### run（Monte Carlo）输出

`{layout, army, trials, seed, grid, destruction:{mean,min,p10,p90,max}, best:{spawn,destruction}, timeline, buildings, hp_destroyed}`

## 命令

```powershell
python tools/wargame_cli.py --layout bases\th16\03\layout.json \
  --army '{"giant":8,"wizard":12,"earthquake":2}' --trials 100 --seed 1
```

（PowerShell 下 JSON 引号可写成 `--army '{"giant":8}'`，或直接用 Python 调用 `wargame.run`。）

## 实测（2026-11-26，base 03）

- 军队 `{giant:8, wizard:12, earthquake:2}`、trials=40：摧毁率 mean **15.5%**，p10 10.5%，p90 21.1%，best 投放点 (1,22) 22.1%；
- 同布局单次推演（giant 5 + wizard 8）：4/38 建筑，10.5%，耗时 25 秒仿真时间；
- 单次推演 < 50ms（200 trials 约 5–10 秒，CPU）。

## 局限（诚实）

- 数值是近似表（建筑取 `assets.STATS` 的 TH13 基线），只保证相对排序，不代表真实战斗结果；
- 没有英雄技能、陷阱、援军、法术范围细节；墙按单格血量简化；
- 目标选择是「最近」，没有真实寻路与分身，结论用于对比投放点/阵容，不用于预测三星概率。
