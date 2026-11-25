# -*- coding: utf-8 -*-
"""防御结构分析：覆盖图、弱侧定位、候选撒兵方案与研究结论。

输入是 44x44 网格上的建筑清单（人工标注或后续检测结果），输出是可直接拿去做
赛前研究的结构化结论。全部离线运行，不碰游戏客户端。
"""
import math

import cv2
import numpy as np

from . import assets
from .sim import dijkstra_cost, trace_path

SECTOR_COUNT = 16

# 战术价值权重：先拆谁最能削弱整座阵的火力
VALUE_WEIGHT = {
    "eagle-artillery": 10.0, "monolith": 9.0, "scattershot": 8.5,
    "inferno-tower": 8.0, "air-defense": 7.0, "x-bow": 6.0,
    "multi-archer-tower": 5.5, "wizard-tower": 5.0, "bomb-tower": 4.5,
    "air-sweeper": 4.0, "hidden-tesla": 4.0, "spell-tower": 3.5,
    "mortar": 3.0, "archer-tower": 3.0, "cannon": 2.5,
    "firespitter": 6.5, "town-hall": 12.0,
}


def _ring_cells(ring):
    xs, ys = np.where(ring.astype(bool))
    return list(zip(xs.tolist(), ys.tolist()))


def _dilate(mask, k):
    out = mask.copy()
    for _ in range(k):
        nxt = out.copy()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                nxt |= np.roll(np.roll(out, dx, axis=0), dy, axis=1)
        out = nxt
    return out


def _morph_close(mask, k=9):
    """闭运算：先膨胀再腐蚀，填掉城内小于核的空隙，保持外轮廓。"""
    kernel = np.ones((k, k), np.uint8)
    closed = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_CLOSE, kernel, iterations=1)
    return closed.astype(bool)


def deployment_ring(sim, margin=1):
    """可撒兵区：占位（建筑格+围墙格）闭运算填空隙后膨胀，取反，再去掉地图最外一圈。

    旧实现把建筑包围盒整块扣掉，会误删"围墙外、建筑与地图边之间"的合法撒兵格；
    改为只封锁真正被建筑/围墙占住的区域，不再按包围盒一刀切。
    """
    n = sim.n
    occ = np.zeros((n + 1, n + 1), dtype=bool)
    for b in sim.buildings:
        st = assets.STATS.get(b["type"], {})
        k = max(1, int(st.get("size", 3)))
        x, y = b["tile"]
        for dx in range(-k // 2, k // 2 + 1):
            for dy in range(-k // 2, k // 2 + 1):
                nx, ny = int(x + dx), int(y + dy)
                if 0 <= nx <= n and 0 <= ny <= n:
                    occ[nx, ny] = True
    # 围墙格同样占位（围墙是防线的一部分，不是空地）
    occ |= sim.wall.astype(bool)
    closed = _morph_close(occ, 9)
    blocked = _dilate(closed, margin)
    ring = ~blocked
    # 地图最外一圈（grid 边界）不允许撒兵
    ring[0, :] = ring[:, 0] = ring[n, :] = ring[:, n] = False
    return ring


def coverage_map(sim):
    """每个格子受到的总防御 dps，即覆盖图。"""
    return sim.dps.copy()


def sector_entries(sim, ring, army, sectors=SECTOR_COUNT, edge_margin=2):
    """把可用撒兵环按角度分扇区，每区取最优撒兵点。

    边角偏好：同一扇区内非最外环相邻带的格子优先，避免入点被热图推到地图贴边；
    该扇区若全部格子都在边角带，才回退取带内最高分。
    """
    hm = sim.heatmap(ring, army)
    cells = _ring_cells(ring)
    cx = cy = sim.n / 2.0
    buckets = {}
    for (x, y) in cells:
        s = hm[x, y]
        if np.isnan(s):
            continue
        ang = math.degrees(math.atan2(y - cy, x - cx)) % 360
        k = int(ang // (360.0 / sectors))
        band = min(x, y, sim.n - x, sim.n - y) <= edge_margin
        cand = {"sector": k, "angle": round(ang, 1), "tile": (x, y),
                "score": float(s), "cover": float(sim.dps[x, y]), "edge_band": bool(band)}
        cur = buckets.get(k)
        if cur is None or (not band and cur["edge_band"]) or \
                ((band == cur["edge_band"]) and s > cur["score"]):
            buckets[k] = cand
    out = sorted(buckets.values(), key=lambda d: -d["score"])
    return out


def path_profile(sim, start, army):
    """从撒兵点到核心的实际路径与沿途受击。"""
    targets = [b["tile"] for b in sim.buildings if b["dps"] == 0] or \
              ([max(sim.buildings, key=lambda b: b["hp"])["tile"]] if sim.buildings else None)
    cost = dijkstra_cost(sim.n, blocked=sim.occ, wall=sim.wall, wall_cost=8.0, targets=targets)
    path = trace_path(cost, start, sim.n)
    steps = len(path)
    dt = (1.0 / max(army.get("speed", 1.5), 0.2))
    case = [sim.dps[p] for p in path]
    incoming = float(np.sum(case) * dt)
    return {"path": [[int(a), int(b)] for a, b in path], "steps": steps,
            "time_s": round(steps * dt, 1), "exposure": round(incoming, 0)}


def defense_report(sim, ring, army):
    """防御结构体检：核心覆盖、外露高价值目标、盲区、重心。"""
    n = sim.n
    c = int(n / 2)
    core_cover = float(sim.dps[max(0, c - 3):c + 4, max(0, c - 3):c + 4].sum())
    sectors = sector_entries(sim, ring, army)

    # 外露的高价值防御：dps 高且离可撒兵环很近
    rc = _ring_cells(ring)

    def edge_dist(tile):
        return min(abs(tile[0] - x) + abs(tile[1] - y) for (x, y) in rc)

    exposed = []
    for b in sim.buildings:
        if b["dps"] <= 0:
            continue
        d = edge_dist(b["tile"])
        if d <= 5:
            exposed.append({"type": b["type"], "tile": list(b["tile"]), "dps": round(b["dps"]),
                            "edge_dist": int(d)})
    exposed.sort(key=lambda e: -e["dps"])

    # 盲区：覆盖低但离核心不太远的撒兵点
    blind = []
    for (x, y) in rc:
        if sim.dps[x, y] <= 120:
            dist = abs(x - c) + abs(y - c)
            blind.append({"tile": [x, y], "cover": round(float(sim.dps[x, y])),
                          "dist_core": int(dist)})
    blind.sort(key=lambda d: d["dist_core"])

    # 重心：防御 dps 的分布中心，用来判断哪一侧更"重"
    ys, xs = np.where(sim.dps > 0)
    weights = sim.dps[sim.dps > 0]
    if len(xs):
        centroid = (round(float(np.average(xs, weights=weights)), 1),
                    round(float(np.average(ys, weights=weights)), 1))
    else:
        centroid = (n / 2, n / 2)

    best = sectors[0] if sectors else None
    worst = min(sectors, key=lambda s: s["score"]) if sectors else None
    spread = round(float(np.std([s["score"] for s in sectors])), 4) if sectors else 0.0

    notes = []
    if best:
        notes.append(f"最优切入在 {best['angle']:.0f}° 扇区（格 {best['tile'][0]},{best['tile'][1]}），"
                     f"模拟得分 {best['score']:.2f}，该点覆盖 dps {best['cover']:.0f}。")
    if worst:
        notes.append(f"最差切入在 {worst['angle']:.0f}° 扇区，得分 {worst['score']:.2f}；"
                     f"两者差 {best['score'] - worst['score']:.2f}，说明各向防御不均。")
    if exposed:
        e = exposed[0]
        notes.append(f"最外露的高价值防御是 {e['type']}（格 {e['tile'][0]},{e['tile'][1]}，"
                     f"距可撒兵环仅 {e['edge_dist']} 格），可优先用少量兵力牵制。")
    if blind:
        b = blind[0]
        notes.append(f"最近核心的覆盖盲区在格 {b['tile'][0]},{b['tile'][1]}（覆盖 {b['cover']} dps，"
                     f"距核心 {b['dist_core']} 格），适合做主攻突破口。")
    notes.append(f"核心 7x7 区域覆盖 {core_cover:.0f} dps，防御重心在 "
                 f"({centroid[0]},{centroid[1]})，撒兵点应避开重心一侧。")

    # 打击优先级：战术价值 / 可接近程度（越外露越先拆）
    # 实测问题：散射炮(8.5)权重高于防空(7.0)，纯按 value/距离 会把散射炮排首，
    # 违背空军队形"先拆防空"的 doctrine；防空给 1.3 倍优先级加成校正。
    priority = []
    for b in sim.buildings:
        val = VALUE_WEIGHT.get(b["type"], 0)
        if not val:
            continue
        ed = edge_dist(b["tile"])
        boost = 1.3 if b["type"] == "air-defense" else 1.0
        priority.append({"type": b["type"], "tile": list(b["tile"]),
                         "value": val, "edge_dist": ed,
                         "priority": round(val * boost / max(1.0, ed * 0.8), 2)})
    # 排序：防空目标在空军队形里优先开道，给 1.2 的排序加成（仅影响先后展示，
    # 不改 priority 数值）；暴露极近(ed<=3)的高价值目标仍可凭数值领先。
    priority.sort(key=lambda p: -(p["priority"] + (1.2 if p["type"] == "air-defense" else 0.0)))
    if priority:
        head = "；".join(f"{p['type']}({p['tile'][0]},{p['tile'][1]})" for p in priority[:4])
        notes.append(f"建议首打顺序：{head}（越外露越先拆，先削防空再压核心）。")

    return {"core_cover_dps": round(core_cover), "centroid": list(centroid),
            "sectors": sectors, "exposed": exposed[:6], "blind": blind[:8],
            "priority": priority[:5],
            "sector_score_std": spread, "notes": notes}


def candidate_plans(sim, ring, army, report=None, topk=3):
    """生成三类候选方案：单点强攻 / 双线分离 / 弱侧渗透。"""
    report = report or defense_report(sim, ring, army)
    sectors = report["sectors"]
    total_troops = int(army["troops"].get("edrag", 7))
    hm = sim.heatmap(ring, army)

    def profile(tile):
        return path_profile(sim, tuple(tile), army)

    def heat(tile):
        v = hm[int(tile[0]), int(tile[1])]
        return float(v) if not np.isnan(v) else 0.0

    plans = []
    if sectors:
        a = sectors[0]
        p = profile(a["tile"])
        plans.append({
            "id": "A", "name": "单点强攻",
            "entries": [{"tile": list(a["tile"]), "angle": a["angle"], "score": round(a["score"], 3),
                         "troops": total_troops, "share": 1.0}],
            "path": p, "rationale": f"选全图最高分的 {a['angle']:.0f}° 扇区，{total_troops} 只雷龙同一侧压上，"
                                    f"路径 {p['steps']} 格 / 约 {p['time_s']}s，沿途承伤 {p['exposure']:.0f}。",
        })

    if len(sectors) >= 2:
        # 扇区互斥：双线的两个扇区都不得与 A 单点强攻所在扇区重合，
        # 避免 B 的第一入点直接复制 A；两线夹角至少 90° 才称得上分兵。
        a_sec = sectors[0]["sector"] if sectors else None
        pair, best_sum = None, -1.0
        for i in range(len(sectors)):
            for j in range(i + 1, len(sectors)):
                if sectors[i]["sector"] == a_sec or sectors[j]["sector"] == a_sec:
                    continue
                if tuple(sectors[i]["tile"]) == tuple(sectors[j]["tile"]):
                    continue
                da = abs((sectors[i]["angle"] - sectors[j]["angle"] + 180) % 360 - 180)
                if da < 90:
                    continue
                v = sectors[i]["score"] + sectors[j]["score"] + 0.05 * da
                if v > best_sum:
                    pair, best_sum = (sectors[i], sectors[j]), v
        if pair:
            s1, s2 = pair
            n1 = max(1, int(round(total_troops * 0.6)))
            n2 = max(1, total_troops - n1)
            plans.append({
                "id": "B", "name": "双线分离",
                "entries": [
                    {"tile": list(s1["tile"]), "angle": s1["angle"], "score": round(s1["score"], 3),
                     "troops": n1, "share": 0.6},
                    {"tile": list(s2["tile"]), "angle": s2["angle"], "score": round(s2["score"], 3),
                     "troops": n2, "share": 0.4},
                ],
                "path": profile(s1["tile"]),
                "rationale": f"在 {s1['angle']:.0f}° 与 {s2['angle']:.0f}° 两个相对扇区分兵 {n1}+{n2}，"
                             f"迫使守方火力分向，防空与地狱塔难以同时覆盖两侧。",
            })

    if report["blind"]:
        # 弱侧渗透选点避开最外环相邻带：直接在可撒兵环上扫低覆盖(dps<=120)的
        # 非边角格，取距核心最近者；扫不到再回退盲区列表首项。
        n = sim.n
        cc = n / 2.0
        cand = None
        for (x, y) in _ring_cells(ring):
            if sim.dps[x, y] > 120:
                continue
            if min(x, y, n - x, n - y) <= 2:
                continue
            d = abs(x - cc) + abs(y - cc)
            if cand is None or d < cand[0]:
                cand = (d, [x, y])
        if cand is None:
            b = report["blind"][0]
        else:
            bx, by = cand[1]
            b = {"tile": [bx, by], "cover": round(float(sim.dps[bx, by]))}
        p = profile(b["tile"])
        plans.append({
            "id": "C", "name": "弱侧渗透",
            "entries": [{"tile": b["tile"], "angle": None, "score": round(heat(b["tile"]), 3),
                         "troops": total_troops, "share": 1.0}],
            "path": p,
            "rationale": f"从距核心最近的盲区（格 {b['tile'][0]},{b['tile'][1]}，覆盖仅 {b['cover']} dps）"
                         f"切入，先手拆掉核心侧防御，路径 {p['steps']} 格 / {p['time_s']}s。",
        })

    raw_pred = []
    for pl in plans:
        raw = sum(e["score"] for e in pl["entries"]) / max(len(pl["entries"]), 1)
        raw_pred.append(raw)
        pl["predicted_raw"] = round(raw, 3)
        pl["exposure"] = round(pl["path"]["exposure"])

    # 分差再归一：原始热图均值彼此挤在 0.15~0.30，绝对差只有 0.01~0.05，
    # 横向看几乎平手；按同批最优=1.0 归一，保留相对排序、拉开可读差距。
    if plans:
        pmax = max(raw_pred) or 1.0
        for pl, raw in zip(plans, raw_pred):
            pl["predicted"] = round(raw / pmax, 3)

    # 风险用相对口径：同批候选里最省的那条算低，便于横向比较
    if plans:
        emin = min(p["exposure"] for p in plans) or 1
        for pl in plans:
            r = pl["exposure"] / emin
            pl["risk"] = "低" if r <= 1.05 else ("中" if r <= 1.35 else "高")
    plans.sort(key=lambda p: -p["predicted"])
    return plans[:topk]
