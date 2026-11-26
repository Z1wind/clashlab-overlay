# -*- coding: utf-8 -*-
"""赛前兵棋推演引擎：确定性 tick 推演 + Monte Carlo 投放点评估。

设计参考
--------
NathanNT/clash-battle-engine 的「确定性」设计思路：固定 tick 推进、所有随机数
由显式 seed 驱动、同样的 (layout, army, trials, seed) 必然得到同样的结果。
本文件只借鉴这一思路，**没有复制上游任何代码**；开发环境无外网（web 检索
HTTP 401），未逐行核对上游实现，具体算法以本文件与 docs/WARGAME.md 为准。

依赖
----
纯 numpy + 标准库。建筑 hp/dps/range/size 优先复用 clashlab.assets.stats(name, th=16)
（延迟导入；assets 依赖 cv2，导入失败自动回退内置精简表 BUILDING_FALLBACK，
数值口径见 docs/WARGAME.md「数值来源」一节）。

坐标系
------
与仓库既有口径一致（layout_score.footprint_bounds / plan_render.load_footprints）：
layout.json 的 tile 是建筑中心格，footprint 起点 = tile - (size-1)//2，边长 size；
墙是单格 [[x, y], ...]。内部 numpy 数组一律 [y, x] 索引（行 = y）。

用法
----
    from clashlab import wargame
    res = wargame.run("bases/th16/03/layout.json", {"giant": 15, "wizard": 20, "earthquake": 4},
                      trials=200, seed=1)
    one = wargame.simulate_once(layout, army, spawn=(22, 2), seed=0)
"""
from __future__ import annotations

import functools
import json
import math
import multiprocessing as mp
import os
import sys
from collections import deque
from dataclasses import dataclass, field

import numpy as np

__all__ = [
    "TROOPS",
    "SPELLS",
    "DEFAULT_TRIALS",
    "DEFAULT_TICK",
    "DEFAULT_MAX_TIME",
    "DEFAULT_WALL_HP",
    "Layout",
    "building_stats",
    "parse_layout",
    "parse_army",
    "default_spawns",
    "simulate_once",
    "run",
]

DEFAULT_TRIALS = 200
DEFAULT_TICK = 1.0          # 游戏秒 / tick（0.5 可换取更细的时序，代价是耗时翻倍）
DEFAULT_MAX_TIME = 120.0    # 单场最长游戏时间（秒）
DEFAULT_WALL_HP = 6000.0    # 单格墙血量（TH16 近似值，可被参数覆盖）

EARTHQUAKE_RADIUS = 3.5
EARTHQUAKE_PCT = 0.22       # 每发地震对建筑最大血量的百分比（近似）
EARTHQUAKE_MAX_CASTS = 4    # 同建筑最多吃 4 发（游戏内上限的近似）

# ---------------------------------------------------------------------------
# 兵种表（TH16 近似值）
#
# 说明：
# - speed 单位「格/秒」；网格步进实现单 tick 最多走 1 格，故 speed 实际按
#   1/tick = 2.0 封顶，表内已按此取值。
# - range 单位「格」；近战 1.0 = 贴身，远程 3.0~3.5。
# - prefer_defense=True：防御优先（坦克类），先打最近防御，防御清空再打任意建筑。
# - housing 仅作展示，本引擎不校验人口上限。
# ---------------------------------------------------------------------------
TROOPS = {
    "barbarian": {"hp": 230.0,  "dps": 50.0,  "speed": 2.0, "range": 1.0, "prefer_defense": False, "housing": 1},
    "archer":    {"hp": 130.0,  "dps": 45.0,  "speed": 2.0, "range": 3.5, "prefer_defense": False, "housing": 1},
    "giant":     {"hp": 2200.0, "dps": 90.0,  "speed": 1.0, "range": 1.0, "prefer_defense": True,  "housing": 5},
    "wizard":    {"hp": 400.0,  "dps": 200.0, "speed": 1.5, "range": 3.0, "prefer_defense": False, "housing": 4},
    "pekka":     {"hp": 7200.0, "dps": 480.0, "speed": 1.0, "range": 1.0, "prefer_defense": False, "housing": 25},
    "hog-rider": {"hp": 1200.0, "dps": 160.0, "speed": 2.0, "range": 1.0, "prefer_defense": True,  "housing": 5},
    "valkyrie":  {"hp": 1900.0, "dps": 190.0, "speed": 2.0, "range": 1.0, "prefer_defense": False, "housing": 8},
    "golem":     {"hp": 7200.0, "dps": 100.0, "speed": 1.0, "range": 1.0, "prefer_defense": False, "housing": 30},
    "witch":     {"hp": 400.0,  "dps": 160.0, "speed": 1.5, "range": 3.0, "prefer_defense": False, "housing": 12},
    "bowler":    {"hp": 1000.0, "dps": 110.0, "speed": 1.5, "range": 3.0, "prefer_defense": False, "housing": 6},
    "miner":     {"hp": 1200.0, "dps": 130.0, "speed": 2.0, "range": 1.0, "prefer_defense": True,  "housing": 6},
    "yeti":      {"hp": 4000.0, "dps": 200.0, "speed": 1.5, "range": 1.0, "prefer_defense": False, "housing": 18},
}

SPELLS = {
    "earthquake": {"radius": EARTHQUAKE_RADIUS, "pct": EARTHQUAKE_PCT,
                   "max_casts": EARTHQUAKE_MAX_CASTS},
}

DEFAULT_BUILDING = {"hp": 1400.0, "dps": 120.0, "range": 9.0, "size": 3}

# 内置精简表：与 clashlab/assets.py 的 STATS(TH13 基线) + TH16_OVERRIDE 同值。
# assets 可用时以 assets 为准；本表只在 assets 不可导入（例如无 cv2 的极简环境）时兜底。
BUILDING_FALLBACK = {
    "town-hall":        {"hp": 6900.0, "dps": 0.0,   "range": 0.0,  "size": 4},
    "eagle-artillery":  {"hp": 4000.0, "dps": 350.0, "range": 11.0, "size": 3},
    "scattershot":      {"hp": 3000.0, "dps": 290.0, "range": 11.0, "size": 3},
    "inferno-tower":    {"hp": 3200.0, "dps": 250.0, "range": 9.0,  "size": 2},
    "x-bow":            {"hp": 3000.0, "dps": 200.0, "range": 11.0, "size": 3},
    "cannon":           {"hp": 1200.0, "dps": 118.0, "range": 9.0,  "size": 3},
    "archer-tower":     {"hp": 1400.0, "dps": 118.0, "range": 10.0, "size": 3},
    "wizard-tower":     {"hp": 1300.0, "dps": 122.0, "range": 7.0,  "size": 3},
    "air-defense":      {"hp": 1500.0, "dps": 330.0, "range": 10.0, "size": 3},
    "mortar":           {"hp": 1000.0, "dps": 45.0,  "range": 11.0, "size": 3},
    "air-sweeper":      {"hp": 1050.0, "dps": 0.0,   "range": 0.0,  "size": 2},
    "hidden-tesla":     {"hp": 1000.0, "dps": 130.0, "range": 7.0,  "size": 2},
    "bomb-tower":       {"hp": 1600.0, "dps": 90.0,  "range": 6.0,  "size": 3},
    "spell-tower":      {"hp": 2500.0, "dps": 120.0, "range": 8.0,  "size": 2},
    "multi-archer-tower": {"hp": 1600.0, "dps": 140.0, "range": 10.0, "size": 3},
    "monolith":         {"hp": 5353.0, "dps": 193.0, "range": 11.0, "size": 3},
    "firespitter":      {"hp": 4500.0, "dps": 410.0, "range": 16.0, "size": 3},
    "ricochet-cannon":  {"hp": 5700.0, "dps": 390.0, "range": 9.0,  "size": 3},
    "clan-castle":      {"hp": 5600.0, "dps": 0.0,   "range": 0.0,  "size": 3},
    "gold-storage":     {"hp": 3000.0, "dps": 0.0,   "range": 0.0,  "size": 3},
    "elixir-storage":   {"hp": 3000.0, "dps": 0.0,   "range": 0.0,  "size": 3},
    "dark-elixir-storage": {"hp": 3000.0, "dps": 0.0, "range": 0.0, "size": 3},
}


@functools.lru_cache(maxsize=None)
def building_stats(btype):
    """解析建筑数值：assets.stats(name, th=16) 优先，失败回退内置表。

    返回值至少含 hp / dps / range / size 四个键。
    """
    fb = BUILDING_FALLBACK.get(btype) or DEFAULT_BUILDING
    try:
        from .assets import stats as _assets_stats  # 延迟导入：assets 依赖 cv2
        s = _assets_stats(btype, th=16)
        if isinstance(s, dict):
            return {
                "hp": float(s.get("hp", fb["hp"])),
                "dps": float(s.get("dps", fb["dps"])),
                "range": float(s.get("range", fb["range"])),
                "size": int(s.get("size") or fb["size"]),
            }
    except Exception:
        pass
    return {"hp": float(fb["hp"]), "dps": float(fb["dps"]),
            "range": float(fb["range"]), "size": int(fb["size"])}


@dataclass
class Layout:
    """解析后的阵型。内部数组一律 [y, x] 索引。"""
    name: str
    grid: int
    buildings: list
    walls: list
    blocked: np.ndarray
    bld_at: np.ndarray
    passable: np.ndarray
    deployment: np.ndarray
    meta: dict = field(default_factory=dict)


def load_layout(path):
    """读 layout.json（UTF-8），返回原始 dict。"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _deployment_mask(passable, grid, band=2):
    """从地图边界做 4 邻域洪泛，取可通行且离边界 <= band 的格子作为投放区。

    墙/建筑都视为不可通行，因此正常阵型下投放区在墙外；若整图被墙封死导致
    投放区为空，退化为「洪泛可达区」。
    """
    seen = np.zeros((grid, grid), dtype=bool)
    dq = deque()
    for i in range(grid):
        for px, py in ((i, 0), (i, grid - 1), (0, i), (grid - 1, i)):
            if passable[py, px] and not seen[py, px]:
                seen[py, px] = True
                dq.append((px, py))
    while dq:
        x, y = dq.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < grid and 0 <= ny < grid and passable[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                dq.append((nx, ny))
    if not seen.any():
        return passable.copy()
    ys, xs = np.nonzero(seen)
    dist = np.minimum(np.minimum(xs, grid - 1 - xs), np.minimum(ys, grid - 1 - ys))
    mask = np.zeros((grid, grid), dtype=bool)
    sel = dist <= band
    if not sel.any():
        return seen.copy()
    mask[ys[sel], xs[sel]] = True
    return mask


def _guess_th(text):
    import re as _re
    m = _re.search(r"th(\d{1,2})", str(text or ""), _re.I)
    return int(m.group(1)) if m else 16


def _ruleset_size(btype, default=3):
    """从 knowledge/th_ruleset.json 查建筑占地（reviewed）。"""
    try:
        import json as _json
        import os as _os
        _p = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                           "knowledge", "th_ruleset.json")
        if not getattr(_ruleset_size, "_cache", None):
            _ruleset_size._cache = _json.load(open(_p, encoding="utf-8")).get("objects") or {}
        o = _ruleset_size._cache.get(str(btype)) or {}
        w = int(o.get("width") or 0)
        h = int(o.get("height") or 0)
        return max(w, h) or default
    except Exception:
        return default


def _is_defense_type(btype):
    """只有 assets.STATS / TH16_OVERRIDE 里的类型算防御；经济/兵营/陷阱按非防御。"""
    try:
        from . import assets as _assets
        return (str(btype) in _assets.STATS) or (str(btype) in getattr(_assets, "TH16_OVERRIDE", {}))
    except Exception:
        return False


def parse_layout(data):
    """把 layout dict / 路径 / 已解析对象统一成 Layout。"""
    if isinstance(data, Layout):
        return data
    raw_name = None
    if isinstance(data, (str, os.PathLike)):
        raw_name = os.fspath(data)
        data = load_layout(raw_name)
    if not isinstance(data, dict):
        raise TypeError("layout 必须是 dict / 路径 / Layout，收到 %r" % (type(data).__name__,))

    grid = int(data.get("grid") or 0)
    if grid < 2:
        raise ValueError("layout.grid 缺失或非法: %r" % (data.get("grid"),))
    name = str(data.get("name") or (raw_name or "<inline>"))

    buildings = []
    for raw in data.get("buildings") or []:
        if not isinstance(raw, dict):
            continue
        typ = str(raw.get("type") or "unknown")
        tile = raw.get("tile") or [grid // 2, grid // 2]
        try:
            tx, ty = int(round(float(tile[0]))), int(round(float(tile[1])))
        except Exception:
            tx, ty = grid // 2, grid // 2
        st = building_stats(typ)
        if not _is_defense_type(typ):
            # 经济/兵营等非防御建筑：不参与火力，HP 用通用低值，尺寸查 ruleset
            st = {"hp": 1000.0, "dps": 0.0, "range": 0.0, "size": _ruleset_size(typ)}
        size = int(raw.get("size") or st["size"] or 3)
        size = max(1, min(size, grid))
        hp = float(raw["hp"]) if raw.get("hp") is not None else float(st["hp"])
        dps = float(raw["dps"]) if raw.get("dps") is not None else float(st["dps"])
        rng = float(raw["range"]) if raw.get("range") is not None else float(st["range"])
        lvl = raw.get("level")
        if lvl is not None and raw.get("hp") is None:
            from . import levels as _levels
            _mx = _levels.max_level_of(typ, _guess_th(name))
            _sc = _levels.building_scale(lvl, _mx)
            hp *= float(_sc["hp"])
            dps *= float(_sc["dps"])
        x0 = tx - (size - 1) // 2
        y0 = ty - (size - 1) // 2
        tiles = [(x, y) for x in range(x0, x0 + size) for y in range(y0, y0 + size)
                 if 0 <= x < grid and 0 <= y < grid]
        if not tiles:
            # 完全越界的脏数据：夹到图内，仍保留可被攻击/计摧毁
            cx = min(max(tx, 0), grid - 1)
            cy = min(max(ty, 0), grid - 1)
            tiles = [(cx, cy)]
        center = (x0 + (size - 1) / 2.0, y0 + (size - 1) / 2.0)
        buildings.append({
            "index": len(buildings),
            "type": typ,
            "tile": [tx, ty],
            "size": size,
            "hp": max(1.0, hp),
            "dps": max(0.0, dps),
            "range": max(0.0, rng),
            "tiles": tiles,
            "center": center,
            "source": raw.get("source"),
            "level": (int(lvl) if lvl is not None else None),
        })

    blocked = np.zeros((grid, grid), dtype=bool)
    bld_at = np.full((grid, grid), -1, dtype=np.int32)
    for bi, bd in enumerate(buildings):
        for (x, y) in bd["tiles"]:
            blocked[y, x] = True
            bld_at[y, x] = bi

    walls = []
    seen_wall = set()
    for w in data.get("walls") or []:
        try:
            x, y = int(round(float(w[0]))), int(round(float(w[1])))
        except Exception:
            continue
        if not (0 <= x < grid and 0 <= y < grid):
            continue
        if (x, y) in seen_wall:
            continue
        if bld_at[y, x] >= 0:      # 建筑底下的墙视为不存在（数据重叠兜底）
            continue
        seen_wall.add((x, y))
        walls.append((x, y))
        blocked[y, x] = True

    passable = ~blocked
    deployment = _deployment_mask(passable, grid)
    return Layout(name=name, grid=grid, buildings=buildings, walls=walls,
                  blocked=blocked, bld_at=bld_at, passable=passable,
                  deployment=deployment, meta={"raw_name": raw_name})


def parse_army(spec):
    """校验并规范化军队构成。返回 {type: count}（保留输入顺序）。"""
    if isinstance(spec, str):
        spec = json.loads(spec)
    if not isinstance(spec, dict) or not spec:
        raise ValueError("army 必须是非空 dict，例如 {'giant': 15, 'wizard': 20}")
    out = {}
    unknown = []
    for k, v in spec.items():
        key = str(k)
        if key in TROOPS or key in SPELLS:
            try:
                n = int(v)
            except Exception:
                raise ValueError("army[%r] 数量非法: %r" % (key, v))
            if n < 0 or n != float(v):
                raise ValueError("army[%r] 必须是非负整数，收到 %r" % (key, v))
            if n > 0:
                out[key] = n
        else:
            unknown.append(key)
    if unknown:
        valid = ", ".join(sorted(TROOPS))
        spells = ", ".join(sorted(SPELLS))
        raise ValueError("未知兵种/法术: %s；可用兵种: %s；可用法术: %s"
                         % (unknown, valid, spells))
    if not out:
        raise ValueError("army 为空（数量全为 0）")
    return out


def _snap(pos, mask, grid, max_r=8):
    """把浮点坐标吸附到最近的 mask=True 格；找不到返回 None（确定性顺序）。"""
    x = int(round(float(pos[0])))
    y = int(round(float(pos[1])))
    x = min(max(x, 0), grid - 1)
    y = min(max(y, 0), grid - 1)
    if mask[y, x]:
        return (x, y)
    best = None
    for r in range(1, max_r + 1):
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if max(abs(dx), abs(dy)) != r:
                    continue
                nx, ny = x + dx, y + dy
                if not (0 <= nx < grid and 0 <= ny < grid):
                    continue
                if not mask[ny, nx]:
                    continue
                d2 = dx * dx + dy * dy
                cand = (d2, nx, ny)
                if best is None or cand < best:
                    best = cand
        if best is not None:
            return (best[1], best[2])
    return None


def default_spawns(layout):
    """8 个候选投放点（四角 + 四边中点），吸附到投放区。"""
    L = layout if isinstance(layout, Layout) else parse_layout(layout)
    n = L.grid
    margin = 1
    mid = n // 2
    anchors = [
        (margin, margin), (n - 1 - margin, margin),
        (margin, n - 1 - margin), (n - 1 - margin, n - 1 - margin),
        (mid, margin), (mid, n - 1 - margin),
        (margin, mid), (n - 1 - margin, mid),
    ]
    out = []
    seen = set()
    for a in anchors:
        p = _snap(a, L.deployment, n, max_r=n)
        if p is None or p in seen:
            continue
        seen.add(p)
        out.append(p)
    if not out:
        # 退化：用可通行格
        for a in anchors:
            p = _snap(a, L.passable, n, max_r=n)
            if p is not None and p not in seen:
                seen.add(p)
                out.append(p)
    if not out:
        raise ValueError("layout 没有任何可部署格（整图被墙/建筑占满？）")
    return out


def _expand_units(army, space, spawn, rng, grid, troop_levels=None, hero_levels=None):
    """按军队构成展开成逐兵数组。

    space 是可站立格掩膜（调用方传 passable：投放抖动只吸附到可站立格，
    显式 spawn 不被投放区约束，便于单测与「指定撒兵点」用法）。
    """
    names = []
    for name, count in army.items():
        if name in TROOPS:
            names.extend([name] * int(count))
    U = len(names)
    pos = np.zeros((U, 2), dtype=np.int64)
    hp = np.zeros(U, dtype=np.float64)
    dps = np.zeros(U, dtype=np.float64)
    speed = np.zeros(U, dtype=np.float64)
    rng_ = np.zeros(U, dtype=np.float64)
    prefer = np.zeros(U, dtype=bool)
    hero_boost = 1.0
    if hero_levels:
        from . import levels as _levels
        hero_boost = float(_levels.army_boost(hero_levels))
    for i, name in enumerate(names):
        st = TROOPS[name]
        jx, jy = rng.uniform(-1.6, 1.6, size=2)
        p = _snap((spawn[0] + jx, spawn[1] + jy), space, grid, max_r=6)
        if p is None:
            p = _snap(spawn, space, grid, max_r=grid) or (int(spawn[0]), int(spawn[1]))
        pos[i] = p
        hp_i, dps_i = float(st["hp"]), float(st["dps"])
        if troop_levels:
            _lv = dict(troop_levels).get(name)
            if _lv is not None:
                from . import levels as _levels
                _sc = _levels.troop_scale(_lv)
                hp_i *= float(_sc["hp"])
                dps_i *= float(_sc["dps"])
        hp[i] = hp_i
        dps[i] = dps_i * hero_boost
        speed[i] = float(st["speed"])
        rng_[i] = float(st["range"])
        prefer[i] = bool(st["prefer_defense"])
    return names, pos, hp, dps, speed, rng_, prefer


def _cast_earthquakes(b_hp, b_max, b_center, b_half, count, events, collect_events):
    """开局法术：每发地震选「预期伤害最大」的建筑中心，命中半径内全部建筑。

    近似：每发打掉目标最大血量的 EARTHQUAKE_PCT，同建筑最多吃 4 发；不建模
    施法延迟/弹道/地形。命中判定用「中心距 - 目标半尺寸 <= 半径」。
    """
    cfg = SPELLS["earthquake"]
    casts = min(int(count), int(cfg["max_casts"]))
    if casts <= 0 or b_hp.size == 0:
        return 0.0
    dx = b_center[:, 0][:, None] - b_center[:, 0][None, :]
    dy = b_center[:, 1][:, None] - b_center[:, 1][None, :]
    edge = np.hypot(dx, dy) - b_half[None, :]
    hit_mat = edge <= cfg["radius"]
    cap = cfg["pct"] * b_max
    total = 0.0
    for cast_i in range(casts):
        alive = b_hp > 0
        if not alive.any():
            break
        per_b = np.where(alive, np.minimum(b_hp, cap), 0.0)
        scores = hit_mat @ per_b
        scores[~alive] = -1.0
        bi = int(np.argmax(scores))
        hits = alive & hit_mat[bi]
        dmg = np.minimum(b_hp[hits], cap[hits])
        b_hp[hits] -= dmg
        total += float(dmg.sum())
        if collect_events:
            events.append({
                "t": 0.0,
                "event": "spell",
                "detail": "earthquake #%d center=(%.1f,%.1f) hits=%d damage=%.0f"
                          % (cast_i + 1, b_center[bi, 0], b_center[bi, 1], int(hits.sum()), float(dmg.sum())),
            })
    return total



def _norm_spawn_list(spawn):
    """把 spawn 归一成点列表：支持单点 (x,y) 或线/区域 [(x,y),(x,y)...]。"""
    if (isinstance(spawn, (list, tuple)) and len(spawn) >= 1
            and all(isinstance(p, (list, tuple)) and len(p) == 2 for p in spawn)):
        return [(int(round(float(p[0]))), int(round(float(p[1])))) for p in spawn]
    return [(int(round(float(spawn[0]))), int(round(float(spawn[1]))))]


def _expand_units_multi(army, spawns, space, rng, grid, troop_levels=None, hero_levels=None):
    """按 spawn 数量拆分军队后逐个展开，返回拼接后的数组（线/区域投放）。"""
    n = max(1, len(spawns))
    parts = []
    for si, sp in enumerate(spawns):
        sub = {}
        for name, count in army.items():
            c = int(count)
            base_c = c // n + (1 if si < (c % n) else 0)
            if base_c > 0:
                sub[name] = base_c
        if sub:
            parts.append(_expand_units(sub, space, sp, rng, grid,
                                       troop_levels=troop_levels, hero_levels=hero_levels))
    if not parts:
        return _expand_units(army, space, spawns[0], rng, grid,
                             troop_levels=troop_levels, hero_levels=hero_levels)
    names = []
    for part in parts:
        names.extend(part[0])
    return (names,) + tuple(np.concatenate([part[k] for part in parts]) for k in range(1, 7))


def simulate_once(layout, army, *, spawn=(2, 2), seed=0, tick=DEFAULT_TICK,
                  max_time=DEFAULT_MAX_TIME, wall_hp=DEFAULT_WALL_HP,
                  troop_levels=None, hero_levels=None,
                  collect_events=True):
    """跑一场确定性推演，返回单场结果 dict。

    参数
    ----
    layout : dict / 路径 / Layout
    army   : dict 或 JSON 字符串，例如 {"giant": 15, "wizard": 20, "earthquake": 4}
    spawn  : 投放点 (x, y)，整数格
    seed   : 随机种子（只影响投放抖动；同 seed 同结果）；可传 tuple
    tick   : 步长（游戏秒）
    max_time : 单场最长游戏时间
    wall_hp  : 单格墙血量
    collect_events : 是否收集 timeline（MC 批量时关掉以提速）

    返回
    ----
    dict: destruction(按栋数百分比) / hp_destroyed / buildings_destroyed /
          buildings_total / units_alive / walls{destroyed,total,hp_remaining} /
          time / end_reason / events
    """
    if tick <= 0:
        raise ValueError("tick 必须 > 0")
    if max_time <= 0:
        raise ValueError("max_time 必须 > 0")
    if wall_hp <= 0:
        raise ValueError("wall_hp 必须 > 0")

    L = layout if isinstance(layout, Layout) else parse_layout(layout)
    army_p = parse_army(army)
    grid = L.grid
    n_b = len(L.buildings)

    b_hp = np.array([bd["hp"] for bd in L.buildings], dtype=np.float64)
    b_max = b_hp.copy()
    b_dps = np.array([bd["dps"] for bd in L.buildings], dtype=np.float64)
    b_rng = np.array([bd["range"] for bd in L.buildings], dtype=np.float64)
    b_size = np.array([bd["size"] for bd in L.buildings], dtype=np.float64)
    b_half = (b_size - 1.0) * 0.5
    b_rng2 = b_rng * b_rng
    b_center = np.array([bd["center"] for bd in L.buildings], dtype=np.float64).reshape(-1, 2)
    b_dead = np.zeros(n_b, dtype=bool)

    # 边界填充一层「假墙」，移动时不用再判越界
    P = grid + 2
    blocked_pad = np.ones((P, P), dtype=bool)
    blocked_pad[1:-1, 1:-1] = L.blocked
    bld_pad = np.full((P, P), -1, dtype=np.int32)
    bld_pad[1:-1, 1:-1] = L.bld_at
    wall_hp_flat = np.zeros(P * P, dtype=np.float64)
    for (x, y) in L.walls:
        wall_hp_flat[(y + 1) * P + (x + 1)] = float(wall_hp)
    wall_hp_pad = wall_hp_flat.reshape(P, P)
    wall_alive_flat = wall_hp_flat > 0
    walls_total = int(wall_alive_flat.sum())
    walls_destroyed = 0
    wall_events_shown = 0

    events = []
    rng = np.random.default_rng(seed)
    spawns = _norm_spawn_list(spawn)
    names, u_pos, u_hp, u_dps, u_speed, u_range, u_prefer = _expand_units_multi(
        army_p, spawns, L.passable, rng, grid,
        troop_levels=troop_levels, hero_levels=hero_levels)
    U = len(names)
    rows_all = np.arange(max(U, n_b), dtype=np.int64)
    if collect_events:
        events.append({
            "t": 0.0,
            "event": "deploy",
            "detail": ("spawn=(%d,%d) units=%d" % (int(spawns[0][0]), int(spawns[0][1]), U)
                       if len(spawns) == 1 else
                       "spawn_line=[%s] units=%d" % (",".join("%d,%d" % s for s in spawns), U)),
        })

    def_state = [int(((b_hp > 0) & (b_dps > 0) & (b_rng > 0)).sum())]
    def_idx = np.flatnonzero((b_dps > 0) & (b_rng > 0))

    def _reap(t):
        """把 hp<=0 的建筑标记摧毁并释放格子（内部函数，热路径内联调用）。"""
        nonlocal def_idx
        for bidx in np.flatnonzero((b_hp <= 0) & (~b_dead)):
            b_dead[bidx] = True
            bd = L.buildings[int(bidx)]
            for (x, y) in bd["tiles"]:
                blocked_pad[y + 1, x + 1] = False
                bld_pad[y + 1, x + 1] = -1
            if bd["dps"] > 0 and bd["range"] > 0:
                def_state[0] -= 1
            if collect_events:
                events.append({
                    "t": round(float(t), 3),
                    "event": "building_destroyed",
                    "detail": "%s at (%d,%d)" % (bd["type"], bd["tile"][0], bd["tile"][1]),
                })
        if def_idx.size:
            def_idx = def_idx[b_hp[def_idx] > 0]

    # 开局法术
    eq_casts = int(army_p.get("earthquake", 0))
    if eq_casts > 0:
        _cast_earthquakes(b_hp, b_max, b_center, b_half, eq_casts, events, collect_events)
        _reap(0.0)

    speed_slots = max(1, int(math.ceil(float(u_speed.max()) * float(tick)))) if U else 1
    u_budget = np.zeros(U, dtype=np.float64)
    b_dmg = np.zeros(n_b, dtype=np.float64)
    u_dmg = np.zeros(U, dtype=np.float64)
    wall_dmg_flat = np.zeros(P * P, dtype=np.float64)

    dt = float(tick)
    n_ticks = int(math.ceil(max_time / dt - 1e-9))
    last_t = 0.0
    end_reason = "time_limit"
    prev_def = def_state[0]

    for _k in range(n_ticks):
        ui = np.flatnonzero(u_hp > 0)
        if ui.size == 0:
            end_reason = "all_troops_dead"
            break
        bi = np.flatnonzero(b_hp > 0)
        if bi.size == 0:
            end_reason = "all_buildings_destroyed"
            break
        t = (_k + 1) * dt

        upos = u_pos[ui].astype(np.float64)
        diff = upos[:, None, :] - b_center[bi][None, :, :]
        d2 = np.einsum("ijk,ijk->ij", diff, diff)
        eff = u_range[ui][:, None] + b_half[bi][None, :]

        tj = d2.argmin(axis=1)
        pref_rows = u_prefer[ui]
        if pref_rows.any():
            is_def = (b_dps[bi] > 0) & (b_rng[bi] > 0)
            if is_def.any():
                dcols = np.flatnonzero(is_def)
                tj = np.where(pref_rows, dcols[d2[:, dcols].argmin(axis=1)], tj)
        rows = rows_all[:ui.size]
        b_tgt = bi[tj]
        in_r = d2[rows, tj] <= eff[rows, tj] ** 2

        # 1) 部队对建筑（bincount 累计，避免 np.add.at 的慢路径）
        if in_r.any():
            b_dmg += np.bincount(b_tgt[in_r], weights=u_dps[ui[in_r]] * dt, minlength=n_b)

        # 2) 防御对射程内最近的部队
        if def_idx.size and ui.size:
            ddiff = b_center[def_idx][:, None, :] - upos[None, :, :]
            dd2 = np.einsum("ijk,ijk->ij", ddiff, ddiff)
            inr = dd2 <= b_rng2[def_idx][:, None]
            if inr.any():
                tju = np.where(inr, dd2, np.inf).argmin(axis=1)
                hit = inr.any(axis=1)
                u_dmg += np.bincount(ui[tju[hit]], weights=b_dps[def_idx][hit] * dt,
                                     minlength=U)

        # 3) 移动（网格步进；遇墙/建筑则攻击阻挡物）
        #    每 tick 允许 ceil(最快兵速*dt) 次步进，使 dt 变化时「格/秒」语义不变；
        #    被阻挡的单位每 tick 只出手一次（blocked_done），避免多槽重复打墙。
        mover0 = ~in_r
        if mover0.any():
            u_budget[ui[mover0]] += u_speed[ui[mover0]] * dt
            blocked_done = np.zeros(ui.size, dtype=bool)
            for _slot in range(speed_slots):
                cand = mover0 & (~blocked_done)
                if not cand.any():
                    break
                sel0 = np.flatnonzero(cand)
                if not (u_budget[ui[sel0]] >= 1.0).any():
                    break
                sel = sel0[u_budget[ui[sel0]] >= 1.0]
                ri = ui[sel]
                tgtp = b_center[b_tgt[sel]]
                dx = np.sign(tgtp[:, 0] - u_pos[ri, 0]).astype(np.int64)
                dy = np.sign(tgtp[:, 1] - u_pos[ri, 1]).astype(np.int64)
                nx = u_pos[ri, 0] + dx
                ny = u_pos[ri, 1] + dy
                pi = ny + 1
                pj = nx + 1
                free = ~blocked_pad[pi, pj]
                if free.any():
                    oi = ri[free]
                    u_pos[oi, 0] = nx[free]
                    u_pos[oi, 1] = ny[free]
                    u_budget[oi] -= 1.0
                blk = ~free
                if blk.any():
                    bp = ri[blk]
                    bx = nx[blk]
                    by = ny[blk]
                    pbi = by + 1
                    pbj = bx + 1
                    wmask = wall_hp_pad[pbi, pbj] > 0
                    if wmask.any():
                        flat = pbi[wmask] * P + pbj[wmask]
                        wall_dmg_flat += np.bincount(flat, weights=u_dps[bp[wmask]] * dt,
                                                     minlength=P * P)
                    nm = ~wmask
                    if nm.any():
                        bt = bld_pad[pbi[nm], pbj[nm]]
                        val = bt >= 0
                        if val.any():
                            b_dmg += np.bincount(bt[val], weights=u_dps[bp[nm][val]] * dt,
                                                 minlength=n_b)
                    blocked_done[sel[blk]] = True
                    u_budget[ri[blk]] = np.minimum(u_budget[ri[blk]], 1.0)

        # 4) 结算伤害
        if u_dmg.any():
            u_hp -= u_dmg
            u_dmg[:] = 0.0
        if b_dmg.any():
            b_hp -= b_dmg
            b_dmg[:] = 0.0
            _reap(t)

        if wall_dmg_flat.any():
            wall_hp_flat -= wall_dmg_flat
            wall_dmg_flat[:] = 0.0
            destroyed_now = wall_alive_flat & (wall_hp_flat <= 0)
            if destroyed_now.any():
                for flat_i in np.flatnonzero(destroyed_now):
                    wall_alive_flat[flat_i] = False
                    wall_hp_flat[flat_i] = 0.0
                    wy, wx = divmod(int(flat_i), P)
                    blocked_pad[wy, wx] = False
                    walls_destroyed += 1
                    if collect_events and wall_events_shown < 10:
                        events.append({"t": round(float(t), 3),
                                       "event": "wall_destroyed",
                                       "detail": "(%d,%d)" % (wx - 1, wy - 1)})
                        wall_events_shown += 1

        if prev_def > 0 and def_state[0] == 0 and collect_events:
            events.append({"t": round(float(t), 3), "event": "defenses_cleared",
                           "detail": "all defensive buildings destroyed"})
        prev_def = def_state[0]

        last_t = t

    b_hp_clamped = np.clip(b_hp, 0.0, b_max)
    destroyed = int((b_hp <= 0).sum())
    destruction = 100.0 * destroyed / n_b if n_b else 0.0
    hp_destroyed = (100.0 * float((b_max - b_hp_clamped).sum()) / float(b_max.sum())
                    if n_b and b_max.sum() > 0 else 0.0)
    units_alive = int((u_hp > 0).sum())
    walls_hp_remaining = float(wall_hp_flat.sum())

    if collect_events:
        events.append({
            "t": round(float(last_t), 3),
            "event": "end",
            "detail": "reason=%s destruction=%.1f%% units_alive=%d buildings=%d/%d walls=%d/%d"
                      % (end_reason, destruction, units_alive, destroyed, n_b,
                         walls_destroyed, walls_total),
        })

    return {
        "destruction": round(float(destruction), 4),
        "hp_destroyed": round(float(hp_destroyed), 4),
        "buildings_destroyed": destroyed,
        "buildings_total": n_b,
        "units_alive": units_alive,
        "units_total": U,
        "walls": {
            "total": walls_total,
            "destroyed": int(walls_destroyed),
            "hp_remaining": round(walls_hp_remaining, 3),
        },
        "time": round(float(last_t), 3),
        "end_reason": end_reason,
        "events": events,
    }


def _trial_chunk(payload):
    """多进程 worker：跑一批 (spawn, seed) 任务，返回 [(destruction, hp_pct, n_destroyed)]。

    每个 trial 的 seed 与串行路径完全一致（seed=(seed, trial_index)），
    所以「分几片跑」不影响结果，只影响墙钟耗时。
    """
    layout, army, tasks, tick, max_time, wall_hp, troop_levels, hero_levels = payload
    out = []
    for spawn, seed_pair in tasks:
        r = simulate_once(layout, army, spawn=spawn, seed=seed_pair, tick=tick,
                          max_time=max_time, wall_hp=wall_hp,
                          troop_levels=troop_levels, hero_levels=hero_levels,
                          collect_events=False)
        out.append((r["destruction"], r["hp_destroyed"], r["buildings_destroyed"]))
    return out


def _run_trials(L, army_p, tasks, tick, max_time, wall_hp, workers=1,
                troop_levels=None, hero_levels=None):
    """跑完全部 trial。workers>1 时用 spawn 进程池按 trial 分片。

    安全约定：调用方脚本必须有 if __name__ == "__main__": 保护（Windows spawn
    会重新导入主模块，否则会递归重跑）。库默认 workers=1 串行，正是为了不让
    这种事故默认发生；CLI 自己有守卫，所以 CLI 默认开进程池。多进程失败会
    自动回退串行，结果完全一致（每个 trial 的 seed 固定为 (seed, trial_index)）。
    """
    workers = max(1, min(int(workers or 1), len(tasks)))
    workers = max(1, min(int(workers), len(tasks)))
    if workers > 1:
        try:
            n = workers
            bounds = [(len(tasks) * k) // n for k in range(n + 1)]
            payloads = [(L, army_p, tasks[bounds[k]:bounds[k + 1]], tick, max_time, wall_hp,
                         troop_levels, hero_levels)
                        for k in range(n) if bounds[k] < bounds[k + 1]]
            ctx = mp.get_context("spawn")
            with ctx.Pool(len(payloads)) as pool:
                parts = pool.map(_trial_chunk, payloads)
            return [row for part in parts for row in part]
        except Exception:
            pass
    rows = []
    for spawn, seed_pair in tasks:
        r = simulate_once(L, army_p, spawn=spawn, seed=seed_pair, tick=tick,
                          max_time=max_time, wall_hp=wall_hp,
                          troop_levels=troop_levels, hero_levels=hero_levels,
                          collect_events=False)
        rows.append((r["destruction"], r["hp_destroyed"], r["buildings_destroyed"]))
    return rows


def _stats(values):
    arr = np.asarray(values, dtype=np.float64)
    return {
        "mean": round(float(arr.mean()), 2),
        "p10": round(float(np.percentile(arr, 10)), 2),
        "p90": round(float(np.percentile(arr, 90)), 2),
        "min": round(float(arr.min()), 2),
        "max": round(float(arr.max()), 2),
    }


def run(layout, army, trials=DEFAULT_TRIALS, seed=1, tick=DEFAULT_TICK,
        max_time=DEFAULT_MAX_TIME, wall_hp=DEFAULT_WALL_HP, workers=1,
        troop_levels=None, hero_levels=None):
    """Monte Carlo：分层抽样投放点，输出摧毁率分布与最佳投放点。

    分层规则：第 i 次 trial 用候选投放点[i % 候选数]，保证每个投放点机会均等；
    随机性只来自投放抖动（同一 seed 完全复现）。destruction 是「按栋数百分比」
    （CoC 口径），另给 hp_destroyed 作为血量口径。
    """
    if int(trials) < 1:
        raise ValueError("trials 必须 >= 1")
    trials = int(trials)
    L = layout if isinstance(layout, Layout) else parse_layout(layout)
    army_p = parse_army(army)
    spawns = default_spawns(L)

    tasks = [(spawns[i % len(spawns)], (int(seed), i)) for i in range(trials)]
    rows = _run_trials(L, army_p, tasks, tick, max_time, wall_hp, workers=workers,
                       troop_levels=troop_levels, hero_levels=hero_levels)
    destructions = [r[0] for r in rows]
    hp_pcts = [r[1] for r in rows]
    destroyed_counts = [r[2] for r in rows]
    groups = {}      # spawn_idx -> [destruction...]
    hp_groups = {}   # spawn_idx -> [hp_pct...]
    for i, row in enumerate(rows):
        si = i % len(spawns)
        groups.setdefault(si, []).append(row[0])
        hp_groups.setdefault(si, []).append(row[1])

    # 最佳投放点：先比平均摧毁率，再比平均血量摧毁率，最后取更小的 spawn 序号
    best_si = None
    best_key = None
    for si in sorted(groups):
        key = (float(np.mean(groups[si])), float(np.mean(hp_groups[si])), -si)
        if best_key is None or key > best_key:
            best_key = key
            best_si = si
    best_spawn = spawns[best_si]
    best_mean = float(np.mean(groups[best_si]))

    # 最佳投放点下挑「摧毁率最高」的实跑，复跑一次收集 timeline
    cand_idx = [i for i in range(trials) if i % len(spawns) == best_si]
    best_trial = max(cand_idx, key=lambda i: (destructions[i], -i))
    best_run = simulate_once(L, army_p, spawn=best_spawn, seed=(int(seed), best_trial),
                             tick=tick, max_time=max_time, wall_hp=wall_hp,
                             troop_levels=troop_levels, hero_levels=hero_levels,
                             collect_events=True)

    label = L.meta.get("raw_name") or L.name
    return {
        "layout": label,
        "army": army_p,
        "trials": trials,
        "destruction": _stats(destructions),
        "best": {"spawn": [int(best_spawn[0]), int(best_spawn[1])],
                 "destruction": round(best_mean, 2)},
        "timeline": best_run["events"],
        "seed": int(seed),
        "grid": int(L.grid),
        "buildings": {
            "total": int(best_run["buildings_total"]),
            "destroyed_mean": round(float(np.mean(destroyed_counts)), 2),
        },
        "hp_destroyed": {"mean": round(float(np.mean(hp_pcts)), 2)},
    }
