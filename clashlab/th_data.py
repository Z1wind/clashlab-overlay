# -*- coding: utf-8 -*-
"""全大本营（TH1–TH19）数据层：逐档元数据 + 防御数值 + 可信度标注。

为什么单独一层
--------------
识别/评分/兵棋只需要「这档 TH 的建筑大概多少血、多少 dps、占几格、是否已解锁」，
但仓库里只有两套数：`assets.STATS`（TH13 基线，只做相对排序）和
`assets.TH16_OVERRIDE`（TH16 四类新建筑，wiki 口径）。本模块把「档位」显式化：
每档 TH 一张表，查不到就回退到不高于该档的最近档，并把 `approx=True` 写进返回值，
调用方不需要猜自己拿到的是不是近似值。

数据来源（按可信度排序）
------------------------
1. **几何 / 解锁 / 最高等级（TH1–TH19）**：本地 vendored 的上游 ruleset
   `out/overlay/_p3a/upstream/clash-of-clans-base-validator-main/rulesets/home-2026-11-17.json`
   （`review_status: reviewed`，`verified_on: 2026-11-17`，`asset_build: 19.32.5`，
   fact_review 记录检查了 2128 个 per-TH 等级值与 112 个 footprint 维度）。
   本文件把用到的子集内联成静态表（`SIZE` / `UNLOCKED` / `LEVELS`），运行时不依赖 out/ 下的副本。
2. **TH13 的 hp/dps/range/level**：沿用 `assets.STATS`（其自带注释即写明「只用于相对排序，
   不追求逐级精确」）。
3. **TH16 的 hp/dps/range/level**：沿用 `assets.STATS` + `assets.TH16_OVERRIDE`，
   逐项不变（这是「TH16 不回归」的硬约束，见 tests/test_th_data.py::TestTh16Unchanged）。
4. **TH17–TH19 的 hp/dps/range**：本机无外网（2026-11-26 实测 web 抓取不可用），
   没有逐级官方数值。做法是：以 TH16 快照记录等级为基准，用 reviewed 的「该档最高等级」
   求等级差 Δ，按 hp × 1.07^Δ、dps × 1.08^Δ 外推，range 不变；
   全部 `confidence="low"`，并在 `note` 里写明公式与 Δ —— 不允许「看起来像真值」的裸数字。

返回约定
--------
`stats(name, th)` 返回 dict，必含 `hp` / `dps` / `range`，并带：
  - `th`：请求的档位；
  - `approx`：True 表示数值来自更低的档（或通用兜底），不是该档的精确表；
  - `approx_from`：实际取数的档位（None = 没有任何档位记录，用了通用兜底）；
  - `source` / `confidence`：这一条数值的来源与置信度（high / medium / low）；
  - `unknown`：True 表示该建筑在所有数据源里都不存在（名字拼错/新建筑未登记）；
  - `size` / `level`：能确定时给出（TH17–19 的 size/level 直接取 reviewed 表）。
"""
from __future__ import annotations

import logging

from . import assets

_log = logging.getLogger("clashlab.th_data")

#: 大本营网格边长（格）。reviewed board 约定，所有档位一致。
GRID_SIZE = 44
#: 大本营占格（所有档位一致）。
TOWN_HALL_SIZE = 4
#: 支持的档位（1..19）。
SUPPORTED_TOWN_HALLS = tuple(range(1, 20))

#: 内联数据的上游出处（便于审计/复核，不参与运行）。
RULESET = {
    "id": "home-2026-11-17",
    "review_status": "reviewed",
    "verified_on": "2026-11-17",
    "asset_build": "19.32.5",
    "path": "out/overlay/_p3a/upstream/clash-of-clans-base-validator-main/rulesets/home-2026-11-17.json",
}
RULESET_SOURCE = "coc-base-validator ruleset home-2026-11-17 (reviewed, asset_build 19.32.5)"

#: 建筑占格（reviewed footprint，与档位无关；含陷阱）。
SIZE = {
    "town-hall": 4,
    "clan-castle": 3,
    "gold-storage": 3,
    "elixir-storage": 3,
    "dark-elixir-storage": 3,
    "gold-mine": 3,
    "elixir-collector": 3,
    "dark-elixir-drill": 3,
    "army-camp": 4,
    "laboratory": 3,
    "barracks": 3,
    "dark-barracks": 3,
    "spell-factory": 3,
    "dark-spell-factory": 3,
    "workshop": 4,
    "hero-hall": 4,
    "pet-house": 3,
    "blacksmith": 3,
    "builders-hut": 2,
    "bobs-hut": 2,
    "helper-hut": 3,
    "wall": 1,
    "cannon": 3,
    "archer-tower": 3,
    "mortar": 3,
    "air-defense": 3,
    "wizard-tower": 3,
    "hidden-tesla": 2,
    "air-sweeper": 2,
    "bomb-tower": 3,
    "x-bow": 3,
    "inferno-tower": 2,
    "eagle-artillery": 4,
    "scattershot": 3,
    "spell-tower": 2,
    "monolith": 3,
    "multi-archer-tower": 3,
    "ricochet-cannon": 3,
    "multi-gear-tower": 3,
    "firespitter": 3,
    "revenge-tower": 3,
    "super-wizard-tower": 3,
    "crafting-station": 3,
    "bomb": 1,
    "spring-trap": 1,
    "air-bomb": 1,
    "giant-bomb": 2,
    "seeking-air-mine": 1,
    "skeleton-trap": 1,
    "tornado-trap": 1,
    "giga-bomb": 2,
    "hero-banner": 2,
    "squad-barracks": 3,
    "guardian-shrine": 3,
    "spiky-tower": 3,
    "firecracker-tower": 3,
}

#: 各档已解锁建筑（reviewed town_halls[th].limits > 0；不含陷阱，按名称排序）。
UNLOCKED = {
    1: [
        "army-camp",
        "barracks",
        "builders-hut",
        "cannon",
        "elixir-collector",
        "elixir-storage",
        "gold-mine",
        "gold-storage",
        "town-hall",
    ],
    2: [
        "archer-tower",
        "army-camp",
        "barracks",
        "builders-hut",
        "cannon",
        "elixir-collector",
        "elixir-storage",
        "gold-mine",
        "gold-storage",
        "town-hall",
        "wall",
    ],
    3: [
        "archer-tower",
        "army-camp",
        "barracks",
        "builders-hut",
        "cannon",
        "clan-castle",
        "elixir-collector",
        "elixir-storage",
        "gold-mine",
        "gold-storage",
        "laboratory",
        "mortar",
        "town-hall",
        "wall",
    ],
    4: [
        "air-defense",
        "archer-tower",
        "army-camp",
        "barracks",
        "builders-hut",
        "cannon",
        "clan-castle",
        "elixir-collector",
        "elixir-storage",
        "gold-mine",
        "gold-storage",
        "hero-banner",
        "hero-hall",
        "laboratory",
        "mortar",
        "town-hall",
        "wall",
    ],
    5: [
        "air-defense",
        "archer-tower",
        "army-camp",
        "barracks",
        "builders-hut",
        "cannon",
        "clan-castle",
        "elixir-collector",
        "elixir-storage",
        "gold-mine",
        "gold-storage",
        "hero-banner",
        "hero-hall",
        "laboratory",
        "mortar",
        "spell-factory",
        "town-hall",
        "wall",
        "wizard-tower",
    ],
    6: [
        "air-defense",
        "air-sweeper",
        "archer-tower",
        "army-camp",
        "barracks",
        "builders-hut",
        "cannon",
        "clan-castle",
        "elixir-collector",
        "elixir-storage",
        "gold-mine",
        "gold-storage",
        "hero-banner",
        "hero-hall",
        "laboratory",
        "mortar",
        "spell-factory",
        "town-hall",
        "wall",
        "wizard-tower",
    ],
    7: [
        "air-defense",
        "air-sweeper",
        "archer-tower",
        "army-camp",
        "barracks",
        "builders-hut",
        "cannon",
        "clan-castle",
        "dark-barracks",
        "dark-elixir-drill",
        "dark-elixir-storage",
        "elixir-collector",
        "elixir-storage",
        "gold-mine",
        "gold-storage",
        "hero-banner",
        "hero-hall",
        "hidden-tesla",
        "laboratory",
        "mortar",
        "spell-factory",
        "town-hall",
        "wall",
        "wizard-tower",
    ],
    8: [
        "air-defense",
        "air-sweeper",
        "archer-tower",
        "army-camp",
        "barracks",
        "blacksmith",
        "bomb-tower",
        "builders-hut",
        "cannon",
        "clan-castle",
        "dark-barracks",
        "dark-elixir-drill",
        "dark-elixir-storage",
        "dark-spell-factory",
        "elixir-collector",
        "elixir-storage",
        "gold-mine",
        "gold-storage",
        "hero-banner",
        "hero-hall",
        "hidden-tesla",
        "laboratory",
        "mortar",
        "spell-factory",
        "squad-barracks",
        "town-hall",
        "wall",
        "wizard-tower",
    ],
    9: [
        "air-defense",
        "air-sweeper",
        "archer-tower",
        "army-camp",
        "barracks",
        "blacksmith",
        "bomb-tower",
        "builders-hut",
        "cannon",
        "clan-castle",
        "dark-barracks",
        "dark-elixir-drill",
        "dark-elixir-storage",
        "dark-spell-factory",
        "elixir-collector",
        "elixir-storage",
        "gold-mine",
        "gold-storage",
        "helper-hut",
        "hero-banner",
        "hero-hall",
        "hidden-tesla",
        "laboratory",
        "mortar",
        "spell-factory",
        "squad-barracks",
        "town-hall",
        "wall",
        "wizard-tower",
        "x-bow",
    ],
    10: [
        "air-defense",
        "air-sweeper",
        "archer-tower",
        "army-camp",
        "barracks",
        "blacksmith",
        "bobs-hut",
        "bomb-tower",
        "builders-hut",
        "cannon",
        "clan-castle",
        "dark-barracks",
        "dark-elixir-drill",
        "dark-elixir-storage",
        "dark-spell-factory",
        "elixir-collector",
        "elixir-storage",
        "gold-mine",
        "gold-storage",
        "helper-hut",
        "hero-banner",
        "hero-hall",
        "hidden-tesla",
        "inferno-tower",
        "laboratory",
        "mortar",
        "spell-factory",
        "squad-barracks",
        "town-hall",
        "wall",
        "wizard-tower",
        "x-bow",
    ],
    11: [
        "air-defense",
        "air-sweeper",
        "archer-tower",
        "army-camp",
        "barracks",
        "blacksmith",
        "bobs-hut",
        "bomb-tower",
        "builders-hut",
        "cannon",
        "clan-castle",
        "crafting-station",
        "dark-barracks",
        "dark-elixir-drill",
        "dark-elixir-storage",
        "dark-spell-factory",
        "eagle-artillery",
        "elixir-collector",
        "elixir-storage",
        "gold-mine",
        "gold-storage",
        "helper-hut",
        "hero-banner",
        "hero-hall",
        "hidden-tesla",
        "inferno-tower",
        "laboratory",
        "mortar",
        "spell-factory",
        "squad-barracks",
        "town-hall",
        "wall",
        "wizard-tower",
        "x-bow",
    ],
    12: [
        "air-defense",
        "air-sweeper",
        "archer-tower",
        "army-camp",
        "barracks",
        "blacksmith",
        "bobs-hut",
        "bomb-tower",
        "builders-hut",
        "cannon",
        "clan-castle",
        "crafting-station",
        "dark-barracks",
        "dark-elixir-drill",
        "dark-elixir-storage",
        "dark-spell-factory",
        "eagle-artillery",
        "elixir-collector",
        "elixir-storage",
        "gold-mine",
        "gold-storage",
        "helper-hut",
        "hero-banner",
        "hero-hall",
        "hidden-tesla",
        "inferno-tower",
        "laboratory",
        "mortar",
        "spell-factory",
        "squad-barracks",
        "town-hall",
        "wall",
        "wizard-tower",
        "workshop",
        "x-bow",
    ],
    13: [
        "air-defense",
        "air-sweeper",
        "archer-tower",
        "army-camp",
        "barracks",
        "blacksmith",
        "bobs-hut",
        "bomb-tower",
        "builders-hut",
        "cannon",
        "clan-castle",
        "crafting-station",
        "dark-barracks",
        "dark-elixir-drill",
        "dark-elixir-storage",
        "dark-spell-factory",
        "eagle-artillery",
        "elixir-collector",
        "elixir-storage",
        "gold-mine",
        "gold-storage",
        "helper-hut",
        "hero-banner",
        "hero-hall",
        "hidden-tesla",
        "inferno-tower",
        "laboratory",
        "mortar",
        "scattershot",
        "spell-factory",
        "squad-barracks",
        "town-hall",
        "wall",
        "wizard-tower",
        "workshop",
        "x-bow",
    ],
    14: [
        "air-defense",
        "air-sweeper",
        "archer-tower",
        "army-camp",
        "barracks",
        "blacksmith",
        "bobs-hut",
        "bomb-tower",
        "builders-hut",
        "cannon",
        "clan-castle",
        "crafting-station",
        "dark-barracks",
        "dark-elixir-drill",
        "dark-elixir-storage",
        "dark-spell-factory",
        "eagle-artillery",
        "elixir-collector",
        "elixir-storage",
        "gold-mine",
        "gold-storage",
        "helper-hut",
        "hero-banner",
        "hero-hall",
        "hidden-tesla",
        "inferno-tower",
        "laboratory",
        "mortar",
        "pet-house",
        "scattershot",
        "spell-factory",
        "squad-barracks",
        "town-hall",
        "wall",
        "wizard-tower",
        "workshop",
        "x-bow",
    ],
    15: [
        "air-defense",
        "air-sweeper",
        "archer-tower",
        "army-camp",
        "barracks",
        "blacksmith",
        "bobs-hut",
        "bomb-tower",
        "builders-hut",
        "cannon",
        "clan-castle",
        "crafting-station",
        "dark-barracks",
        "dark-elixir-drill",
        "dark-elixir-storage",
        "dark-spell-factory",
        "eagle-artillery",
        "elixir-collector",
        "elixir-storage",
        "gold-mine",
        "gold-storage",
        "helper-hut",
        "hero-banner",
        "hero-hall",
        "hidden-tesla",
        "inferno-tower",
        "laboratory",
        "monolith",
        "mortar",
        "pet-house",
        "scattershot",
        "spell-factory",
        "spell-tower",
        "squad-barracks",
        "town-hall",
        "wall",
        "wizard-tower",
        "workshop",
        "x-bow",
    ],
    16: [
        "air-defense",
        "air-sweeper",
        "archer-tower",
        "army-camp",
        "barracks",
        "blacksmith",
        "bobs-hut",
        "bomb-tower",
        "builders-hut",
        "cannon",
        "clan-castle",
        "crafting-station",
        "dark-barracks",
        "dark-elixir-drill",
        "dark-elixir-storage",
        "dark-spell-factory",
        "eagle-artillery",
        "elixir-collector",
        "elixir-storage",
        "gold-mine",
        "gold-storage",
        "helper-hut",
        "hero-banner",
        "hero-hall",
        "hidden-tesla",
        "inferno-tower",
        "laboratory",
        "monolith",
        "mortar",
        "multi-archer-tower",
        "pet-house",
        "ricochet-cannon",
        "scattershot",
        "spell-factory",
        "spell-tower",
        "squad-barracks",
        "town-hall",
        "wall",
        "wizard-tower",
        "workshop",
        "x-bow",
    ],
    17: [
        "air-defense",
        "air-sweeper",
        "archer-tower",
        "army-camp",
        "barracks",
        "blacksmith",
        "bobs-hut",
        "bomb-tower",
        "builders-hut",
        "cannon",
        "clan-castle",
        "crafting-station",
        "dark-barracks",
        "dark-elixir-drill",
        "dark-elixir-storage",
        "dark-spell-factory",
        "elixir-collector",
        "elixir-storage",
        "firespitter",
        "gold-mine",
        "gold-storage",
        "helper-hut",
        "hero-banner",
        "hero-hall",
        "hidden-tesla",
        "inferno-tower",
        "laboratory",
        "monolith",
        "mortar",
        "multi-archer-tower",
        "multi-gear-tower",
        "pet-house",
        "ricochet-cannon",
        "scattershot",
        "spell-factory",
        "spell-tower",
        "squad-barracks",
        "town-hall",
        "wall",
        "wizard-tower",
        "workshop",
        "x-bow",
    ],
    18: [
        "air-defense",
        "air-sweeper",
        "archer-tower",
        "army-camp",
        "barracks",
        "blacksmith",
        "bobs-hut",
        "bomb-tower",
        "builders-hut",
        "cannon",
        "clan-castle",
        "crafting-station",
        "dark-barracks",
        "dark-elixir-drill",
        "dark-elixir-storage",
        "dark-spell-factory",
        "elixir-collector",
        "elixir-storage",
        "firespitter",
        "gold-mine",
        "gold-storage",
        "helper-hut",
        "hero-banner",
        "hero-hall",
        "hidden-tesla",
        "inferno-tower",
        "laboratory",
        "monolith",
        "mortar",
        "multi-archer-tower",
        "multi-gear-tower",
        "pet-house",
        "revenge-tower",
        "ricochet-cannon",
        "scattershot",
        "spell-factory",
        "spell-tower",
        "squad-barracks",
        "super-wizard-tower",
        "town-hall",
        "wall",
        "wizard-tower",
        "workshop",
        "x-bow",
    ],
    19: [
        "air-defense",
        "air-sweeper",
        "archer-tower",
        "army-camp",
        "barracks",
        "blacksmith",
        "bobs-hut",
        "bomb-tower",
        "builders-hut",
        "cannon",
        "clan-castle",
        "crafting-station",
        "dark-barracks",
        "dark-elixir-drill",
        "dark-elixir-storage",
        "dark-spell-factory",
        "elixir-collector",
        "elixir-storage",
        "firecracker-tower",
        "firespitter",
        "gold-mine",
        "gold-storage",
        "guardian-shrine",
        "helper-hut",
        "hero-banner",
        "hero-hall",
        "hidden-tesla",
        "inferno-tower",
        "laboratory",
        "monolith",
        "mortar",
        "multi-archer-tower",
        "multi-gear-tower",
        "pet-house",
        "revenge-tower",
        "ricochet-cannon",
        "scattershot",
        "spell-factory",
        "spell-tower",
        "spiky-tower",
        "squad-barracks",
        "super-wizard-tower",
        "town-hall",
        "wall",
        "wizard-tower",
        "workshop",
        "x-bow",
    ],
}

#: TH17–TH19 每栋建筑的最高等级（reviewed max_levels；0 表示该档未解锁）。
LEVELS = {
    17: {
        "town-hall": 17,
        "clan-castle": 13,
        "gold-storage": 18,
        "elixir-storage": 18,
        "dark-elixir-storage": 12,
        "gold-mine": 17,
        "elixir-collector": 17,
        "dark-elixir-drill": 11,
        "army-camp": 13,
        "laboratory": 15,
        "barracks": 19,
        "dark-barracks": 13,
        "spell-factory": 10,
        "dark-spell-factory": 8,
        "workshop": 9,
        "hero-hall": 11,
        "pet-house": 11,
        "blacksmith": 10,
        "builders-hut": 7,
        "bobs-hut": 1,
        "helper-hut": 1,
        "wall": 18,
        "cannon": 21,
        "archer-tower": 21,
        "mortar": 17,
        "air-defense": 15,
        "wizard-tower": 17,
        "hidden-tesla": 16,
        "air-sweeper": 7,
        "bomb-tower": 12,
        "x-bow": 12,
        "inferno-tower": 11,
        "eagle-artillery": 7,
        "scattershot": 6,
        "spell-tower": 4,
        "monolith": 4,
        "multi-archer-tower": 3,
        "ricochet-cannon": 3,
        "multi-gear-tower": 2,
        "firespitter": 2,
        "revenge-tower": 0,
        "super-wizard-tower": 0,
        "crafting-station": 1,
        "bomb": 13,
        "spring-trap": 12,
        "air-bomb": 12,
        "giant-bomb": 11,
        "seeking-air-mine": 7,
        "skeleton-trap": 4,
        "tornado-trap": 3,
        "giga-bomb": 3,
        "hero-banner": 1,
        "squad-barracks": 10,
        "guardian-shrine": 0,
        "spiky-tower": 0,
        "firecracker-tower": 0,
    },
    18: {
        "town-hall": 18,
        "clan-castle": 14,
        "gold-storage": 19,
        "elixir-storage": 19,
        "dark-elixir-storage": 13,
        "gold-mine": 18,
        "elixir-collector": 18,
        "dark-elixir-drill": 12,
        "army-camp": 14,
        "laboratory": 16,
        "barracks": 19,
        "dark-barracks": 13,
        "spell-factory": 10,
        "dark-spell-factory": 8,
        "workshop": 9,
        "hero-hall": 12,
        "pet-house": 12,
        "blacksmith": 10,
        "builders-hut": 8,
        "bobs-hut": 1,
        "helper-hut": 1,
        "wall": 19,
        "cannon": 21,
        "archer-tower": 21,
        "mortar": 18,
        "air-defense": 16,
        "wizard-tower": 17,
        "hidden-tesla": 17,
        "air-sweeper": 7,
        "bomb-tower": 13,
        "x-bow": 13,
        "inferno-tower": 12,
        "eagle-artillery": 7,
        "scattershot": 7,
        "spell-tower": 4,
        "monolith": 5,
        "multi-archer-tower": 4,
        "ricochet-cannon": 4,
        "multi-gear-tower": 3,
        "firespitter": 3,
        "revenge-tower": 2,
        "super-wizard-tower": 2,
        "crafting-station": 1,
        "bomb": 14,
        "spring-trap": 13,
        "air-bomb": 13,
        "giant-bomb": 12,
        "seeking-air-mine": 8,
        "skeleton-trap": 5,
        "tornado-trap": 3,
        "giga-bomb": 4,
        "hero-banner": 1,
        "squad-barracks": 11,
        "guardian-shrine": 0,
        "spiky-tower": 0,
        "firecracker-tower": 0,
    },
    19: {
        "town-hall": 19,
        "clan-castle": 15,
        "gold-storage": 20,
        "elixir-storage": 20,
        "dark-elixir-storage": 14,
        "gold-mine": 18,
        "elixir-collector": 18,
        "dark-elixir-drill": 12,
        "army-camp": 14,
        "laboratory": 17,
        "barracks": 19,
        "dark-barracks": 13,
        "spell-factory": 10,
        "dark-spell-factory": 8,
        "workshop": 9,
        "hero-hall": 13,
        "pet-house": 12,
        "blacksmith": 10,
        "builders-hut": 9,
        "bobs-hut": 1,
        "helper-hut": 1,
        "wall": 20,
        "cannon": 21,
        "archer-tower": 21,
        "mortar": 18,
        "air-defense": 17,
        "wizard-tower": 17,
        "hidden-tesla": 18,
        "air-sweeper": 7,
        "bomb-tower": 13,
        "x-bow": 14,
        "inferno-tower": 12,
        "eagle-artillery": 7,
        "scattershot": 7,
        "spell-tower": 4,
        "monolith": 5,
        "multi-archer-tower": 5,
        "ricochet-cannon": 5,
        "multi-gear-tower": 4,
        "firespitter": 3,
        "revenge-tower": 2,
        "super-wizard-tower": 2,
        "crafting-station": 1,
        "bomb": 14,
        "spring-trap": 14,
        "air-bomb": 14,
        "giant-bomb": 12,
        "seeking-air-mine": 8,
        "skeleton-trap": 6,
        "tornado-trap": 3,
        "giga-bomb": 4,
        "hero-banner": 1,
        "squad-barracks": 12,
        "guardian-shrine": 1,
        "spiky-tower": 2,
        "firecracker-tower": 2,
    },
}

#: TH17–19 外推系数（每 +1 级）：hp +7%，dps +8%。见模块 docstring 第 4 条。
HP_GROWTH = 1.07
DPS_GROWTH = 1.08

_SOURCE_STATS = "assets.STATS（TH13 基线，只用于相对排序）"
_SOURCE_TH16 = "assets.TH16_OVERRIDE + assets.STATS"
_SOURCE_EXTRAPOLATED = "内部外推（TH16 快照 × reviewed 等级差）"

#: 每档的（status, confidence, note）；status: exact / approx / unverified。
_TH_STATUS = {
    1: ("unverified", "low", "该档没有 hp/dps 数值表；stats() 回退通用兜底（hp1400/dps120/range9），只保证不越界"),
    2: ("unverified", "low", "该档没有 hp/dps 数值表；stats() 回退通用兜底（hp1400/dps120/range9），只保证不越界"),
    3: ("unverified", "low", "该档没有 hp/dps 数值表；stats() 回退通用兜底（hp1400/dps120/range9），只保证不越界"),
    4: ("unverified", "low", "该档没有 hp/dps 数值表；stats() 回退通用兜底（hp1400/dps120/range9），只保证不越界"),
    5: ("unverified", "low", "该档没有 hp/dps 数值表；stats() 回退通用兜底（hp1400/dps120/range9），只保证不越界"),
    6: ("unverified", "low", "该档没有 hp/dps 数值表；stats() 回退通用兜底（hp1400/dps120/range9），只保证不越界"),
    7: ("unverified", "low", "该档没有 hp/dps 数值表；stats() 回退通用兜底（hp1400/dps120/range9），只保证不越界"),
    8: ("unverified", "low", "该档没有 hp/dps 数值表；stats() 回退通用兜底（hp1400/dps120/range9），只保证不越界"),
    9: ("unverified", "low", "该档没有 hp/dps 数值表；stats() 回退通用兜底（hp1400/dps120/range9），只保证不越界"),
    10: ("unverified", "low", "该档没有 hp/dps 数值表；stats() 回退通用兜底（hp1400/dps120/range9），只保证不越界"),
    11: ("unverified", "low", "该档没有 hp/dps 数值表；stats() 回退通用兜底（hp1400/dps120/range9），只保证不越界"),
    12: ("unverified", "low", "该档没有 hp/dps 数值表；stats() 回退通用兜底（hp1400/dps120/range9），只保证不越界"),
    13: ("approx", "medium", "assets.STATS TH13 基线：只用于相对排序，未逐级校准"),
    14: ("approx", "low", "无独立数值表，hp/dps 回退 TH13 基线（偏低）"),
    15: ("approx", "low", "无独立数值表，hp/dps 回退 TH13 基线（偏低）"),
    16: ("approx", "medium", "TH16_OVERRIDE 的 4 类（monolith/ricochet-cannon/clan-castle 高置信、firespitter 低置信）为 wiki 值；其余 15 类沿用 TH13 基线"),
    17: ("approx", "low", "尺寸/等级/解锁为 reviewed ruleset 精确值；hp/dps 为 TH16 快照按等级差外推"),
    18: ("approx", "low", "尺寸/等级/解锁为 reviewed ruleset 精确值；hp/dps 为 TH16 快照按等级差外推"),
    19: ("approx", "low", "尺寸/等级/解锁为 reviewed ruleset 精确值；hp/dps 为 TH16 快照按等级差外推"),
}


def supported_town_halls():
    """返回支持的 TH 列表（1..19）。"""
    return list(SUPPORTED_TOWN_HALLS)


def _norm_th(th):
    """把 th 规整成 1..19 的 int；None 视为非法（stats 必须显式给档位）。"""
    if th is None:
        raise ValueError("th 必填：1..19")
    t = int(th)
    if t < 1 or t > 19:
        raise ValueError("th 必须在 1..19，收到 %r" % (th,))
    return t


def grid_size(th):
    """该档的网格边长（格）。所有档位一致，返回 44。"""
    _norm_th(th)
    return GRID_SIZE


def _th16_snapshot():
    """TH16 快照：STATS 基线 + TH16_OVERRIDE 覆盖（与 assets.stats(name, th=16) 数值一致）。"""
    snap = {}
    for name, base in assets.STATS.items():
        entry = dict(base)
        entry["source"] = _SOURCE_STATS
        entry["confidence"] = "medium"
        entry["note"] = "TH16 未逐级校准，沿用 TH13 基线（现有行为，保持不变）"
        snap[name] = entry
    for name, over in assets.TH16_OVERRIDE.items():
        entry = dict(snap.get(name, {}))
        entry.update(over)
        entry["source"] = over.get("source_site") or _SOURCE_TH16
        entry["confidence"] = over.get("confidence", "medium")
        snap[name] = entry
    return snap


#: 每个有数值表的档位 -> {建筑名: 数值 dict}。TH17–19 由 _extrapolate() 生成。
STATS_BY_TH = {
    13: {name: dict(base, source=_SOURCE_STATS, confidence="medium",
                   note="TH13 近似值，只用于相对排序；未逐级校准")
         for name, base in assets.STATS.items()},
    16: _th16_snapshot(),
}


def _extrapolate(th):
    """由 TH16 快照 + reviewed 等级差生成 TH17–19 的估计表（全部 low 置信）。"""
    out = {}
    lv_table = LEVELS[th]
    for name, base in STATS_BY_TH[16].items():
        lv0 = base.get("level")
        lv1 = lv_table.get(name)
        delta = 0 if (lv0 is None or not lv1) else max(0, int(lv1) - int(lv0))
        hp = int(round(float(base.get("hp", 0) or 0) * (HP_GROWTH ** delta)))
        dps = int(round(float(base.get("dps", 0) or 0) * (DPS_GROWTH ** delta)))
        entry = {
            "hp": hp,
            "dps": dps,
            "range": base.get("range", 0),
            "level": int(lv1) if lv1 else lv0,
            "size": SIZE.get(name, base.get("size")),
            "source": _SOURCE_EXTRAPOLATED,
            "confidence": "low",
            "note": ("外推：TH16 快照 Lv%s → TH%d 最高 Lv%s（Δ%s）；"
                     "hp×%.2f^Δ、dps×%.2f^Δ，range 不变；非官方数值，仅用于相对排序"
                     % (lv0, th, lv1, delta, HP_GROWTH, DPS_GROWTH)),
        }
        if "cn" in base:
            entry["cn"] = base["cn"]
        out[name] = entry
    return out


for _th in (17, 18, 19):
    STATS_BY_TH[_th] = _extrapolate(_th)

_KNOWN_NAMES = set(SIZE) | set(STATS_BY_TH[16]) | {n for lv in LEVELS.values() for n in lv}

_missing_warned = set()


def town_hall_meta(th):
    """该档元数据：grid / town_hall_size / unlocked / status / confidence / source / note。"""
    t = _norm_th(th)
    status, confidence, note = _TH_STATUS[t]
    return {
        "th": t,
        "grid": GRID_SIZE,
        "town_hall_size": TOWN_HALL_SIZE,
        "unlocked": list(UNLOCKED.get(t, [])),
        "status": status,
        "confidence": confidence,
        "source": RULESET_SOURCE,
        "note": note,
    }


def support_status(th):
    """该档的综合状态：exact / approx / unverified。"""
    return _TH_STATUS[_norm_th(th)][0]


def stats(name, th):
    """按档位取数：优先精确档表，缺失回退「不高于该档的最近档」并标 approx=True。

    未知建筑回退 assets.DEFAULT_FALLBACK，unknown=True（只 WARN 一次）。
    """
    t = _norm_th(th)
    entry = None
    from_th = None
    if name in STATS_BY_TH.get(t, {}):
        entry = dict(STATS_BY_TH[t][name])
        from_th = t
    else:
        for cand in sorted(STATS_BY_TH, reverse=True):
            if cand <= t and name in STATS_BY_TH[cand]:
                entry = dict(STATS_BY_TH[cand][name])
                from_th = cand
                break

    unknown = name not in _KNOWN_NAMES
    if entry is None:
        entry = dict(assets.DEFAULT_FALLBACK)
        entry["source"] = "assets.DEFAULT_FALLBACK（通用兜底）"
        entry["confidence"] = "low"
        if unknown:
            entry["note"] = "该建筑在所有数据源里都没有记录（名字拼错或未登记），回退通用兜底"
            if name not in _missing_warned:
                _missing_warned.add(name)
                _log.warning("th_data.stats: 未知建筑 %r（TH%d），回退 DEFAULT_FALLBACK", name, t)
        else:
            entry["note"] = "该建筑有 reviewed 尺寸/等级，但没有 hp/dps 数值，回退通用兜底"
    elif from_th != t:
        entry["note"] = ("%s；数值回退自 TH%d" % (entry.get("note", ""), from_th)).lstrip("；")

    approx = from_th != t
    # reviewed 表补全：TH17+ 的 size/level 一律用 reviewed 值；TH<13 无快照时补 size。
    if name in SIZE and (t >= 17 or "size" not in entry):
        entry["size"] = SIZE[name]
    if t >= 17 and LEVELS.get(t, {}).get(name):
        entry["level"] = LEVELS[t][name]

    out = dict(entry)
    out["th"] = t
    out["approx"] = approx
    out["approx_from"] = from_th if approx else None
    out["unknown"] = unknown
    return out
