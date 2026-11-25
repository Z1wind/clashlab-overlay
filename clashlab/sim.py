# -*- coding: utf-8 -*-
"""轻量战场模拟器：代价场 + 沿路径衰减，输出相对得分而不是绝对破坏率。

设计目标对齐方案文档第 7.3 节：宁可牺牲绝对精度，也要保证候选计划的排序正确。
"""
import heapq
import numpy as np

NEIGHBORS = [(1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]


def dijkstra_cost(n, blocked=None, wall=None, wall_cost=8.0, targets=None):
    """八邻域代价场；wall 单元代价放大，targets 若给出则多源。"""
    cost = np.full((n + 1, n + 1), np.inf, dtype=np.float32)
    blocked = blocked if blocked is not None else np.zeros_like(cost, dtype=bool)
    heap = []
    if targets is None:
        targets = [(n // 2, n // 2)]
    for (tx, ty) in targets:
        cost[tx, ty] = 0.0
        heap.append((0.0, tx, ty))
    heapq.heapify(heap)

    while heap:
        c, x, y = heapq.heappop(heap)
        if c > cost[x, y]:
            continue
        for dx, dy in NEIGHBORS:
            nx, ny = x + dx, y + dy
            if not (0 <= nx <= n and 0 <= ny <= n):
                continue
            if blocked[nx, ny]:
                continue
            step = 1.4142 if dx and dy else 1.0
            if wall is not None and wall[nx, ny]:
                step *= wall_cost
            nc = c + step
            if nc < cost[nx, ny]:
                cost[nx, ny] = nc
                heapq.heappush(heap, (nc, nx, ny))
    return cost


def trace_path(cost, start, n=44, max_steps=200):
    """沿代价场梯度下降，从撒兵点走到核心。"""
    path = [start]
    cur = start
    for _ in range(max_steps):
        x, y = cur
        best = None
        for dx, dy in NEIGHBORS:
            nx, ny = x + dx, y + dy
            if not (0 <= nx <= n and 0 <= ny <= n):
                continue
            if best is None or cost[nx, ny] < best[0]:
                best = (cost[nx, ny], nx, ny)
        if best is None or best[0] >= cost[x, y]:
            break
        cur = (best[1], best[2])
        path.append(cur)
        if cost[cur] <= 0.5:
            break
    return path


class Simulator:
    """输入建筑清单，输出撒兵点得分与热图。"""

    def __init__(self, n=44):
        self.n = n
        self.buildings = []
        self.occ = np.zeros((n + 1, n + 1), dtype=bool)
        self.wall = np.zeros((n + 1, n + 1), dtype=bool)
        self.dps = np.zeros((n + 1, n + 1), dtype=np.float32)

    # ---------- 构建 ----------
    def add_building(self, btype, tile, hp, dps=0.0, rng=0.0, splash=False):
        x, y = int(round(tile[0])), int(round(tile[1]))
        self.buildings.append({"type": btype, "tile": (x, y), "hp": float(hp),
                               "dps": float(dps), "range": float(rng), "splash": splash})
        self.occ[x, y] = True
        if dps > 0 and rng > 0:
            self._stamp_dps(x, y, dps, rng)

    def add_wall(self, tiles):
        for x, y in tiles:
            if 0 <= x <= self.n and 0 <= y <= self.n:
                self.wall[int(x), int(y)] = True

    def _stamp_dps(self, x, y, dps, rng):
        r = int(np.ceil(rng))
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                nx, ny = x + dx, y + dy
                if not (0 <= nx <= self.n and 0 <= ny <= self.n):
                    continue
                if dx * dx + dy * dy <= rng * rng:
                    self.dps[nx, ny] += dps

    # ---------- 推演 ----------
    def score_spawn(self, spawn, army):
        """army: {"hp": 总血量, "dps": 每秒输出, "speed": 格/秒}"""
        cost = dijkstra_cost(self.n, blocked=self.occ, wall=self.wall,
                             wall_cost=8.0, targets=[b["tile"] for b in self.buildings if b["dps"] == 0] or None)
        path = trace_path(cost, spawn, self.n)
        if len(path) < 2:
            return 0.0, 0.0, path

        dt = 1.0 / max(army.get("speed", 1.5), 0.2)
        hp = army["hp"]
        alive_damage = 0.0
        t_alive = 0.0
        for (x, y) in path:
            incoming = float(self.dps[x, y])
            hp -= incoming * dt
            t_alive += dt
            if hp <= 0:
                break

        total_hp = sum(b["hp"] for b in self.buildings) or 1.0
        dealt = min(army["dps"] * t_alive, total_hp * 1.2)
        score = dealt / total_hp

        # 核心到达奖励：走到大本营附近额外加分
        core = min(self.buildings, key=lambda b: b["hp"] * -1) if self.buildings else None
        if core and len(path) > 3:
            dist = abs(path[-1][0] - core["tile"][0]) + abs(path[-1][1] - core["tile"][1])
            score += max(0.0, 0.15 - dist * 0.01)

        return float(min(score, 2.0)), float(t_alive), path

    def heatmap(self, ring_mask, army):
        """全图一次前向累积：沿代价场梯度方向累加受到的 dps 与耗时，避免逐点跑 Dijkstra。"""
        n = self.n
        core_targets = [b["tile"] for b in self.buildings if b["dps"] == 0] or \
                       ([max(self.buildings, key=lambda b: b["hp"])["tile"]] if self.buildings else None)
        cost = dijkstra_cost(n, blocked=self.occ, wall=self.wall, wall_cost=8.0, targets=core_targets)

        reachable = np.isfinite(cost)
        # 从核心（代价最小）向外累积，保证下游格子的累计值已经算好
        flat_cost = np.where(reachable, cost, np.inf).ravel()
        order = np.argsort(flat_cost, kind="stable")
        dps_acc = np.zeros((n + 1, n + 1), dtype=np.float64)   # 累计 dps*dt
        time_acc = np.zeros((n + 1, n + 1), dtype=np.float64)  # 累计 dt
        inv_speed = 1.0 / max(army.get("speed", 1.5), 0.2)

        for idx in order:
            flat = int(idx)
            if flat < 0:
                continue
            x, y = flat // (n + 1), flat % (n + 1)
            if not reachable[x, y]:
                continue
            c = cost[x, y]
            best_nb = None
            best_c = c
            for dx, dy in NEIGHBORS:
                nx, ny = x + dx, y + dy
                if not (0 <= nx <= n and 0 <= ny <= n):
                    continue
                if cost[nx, ny] < best_c:
                    best_c = cost[nx, ny]
                    best_nb = (nx, ny)
            if best_nb is None:
                dps_acc[x, y] = 0.0
                time_acc[x, y] = 0.0
                continue
            step = 1.4142 if (best_nb[0] != x and best_nb[1] != y) else 1.0
            dt = step * inv_speed
            nx, ny = best_nb
            dps_acc[x, y] = dps_acc[nx, ny] + float(self.dps[x, y]) * dt
            time_acc[x, y] = time_acc[nx, ny] + dt

        total_hp = sum(b["hp"] for b in self.buildings) or 1.0
        hp = float(army["hp"])
        out_dps = float(army["dps"])
        hm = np.full((n + 1, n + 1), np.nan, dtype=np.float32)
        total_time = np.where(time_acc > 1e-6, time_acc, 1e-6)
        avg_dps = dps_acc / total_time
        alive_t = np.minimum(hp / np.maximum(avg_dps, 1e-6), total_time)
        dealt = out_dps * alive_t
        score = np.minimum(dealt / total_hp, 2.0).astype(np.float32)
        # 到达奖励 + 时间成本惩罚：路径越短越接近核心，越值得推荐（避免全挤在地图角落）
        reach_cost = np.where(reachable, cost, 0.0).astype(np.float32)
        bonus = np.clip(0.18 - reach_cost * 0.004, 0.0, 0.18)
        time_factor = np.clip(1.0 - 0.5 * reach_cost / 40.0, 0.45, 1.0)
        score = score * time_factor + bonus
        score[~reachable] = np.nan
        hm = np.where(ring_mask.astype(bool), score, np.nan).astype(np.float32)
        self._tmp_heat = hm
        return hm

    def top_spawns(self, ring_mask, army, k=4, min_sep_deg=50):
        """在热图上取分散的前 k 个点，避免四个点挤在一侧。"""
        hm = self.heatmap(ring_mask, army)
        self._tmp_heat = hm
        pts = np.argwhere(~np.isnan(hm))
        if len(pts) == 0:
            return []
        scored = sorted(((hm[tuple(p)], tuple(p)) for p in pts), key=lambda t: -t[0])
        cx, cy = self.n / 2, self.n / 2
        picked = []
        for score, p in scored:
            ang = np.degrees(np.arctan2(p[1] - cy, p[0] - cx))
            if all(abs(((ang - it[1] + 180) % 360) - 180) >= min_sep_deg for it in picked):
                picked.append((score, ang, p))
            if len(picked) >= k:
                break
        return [{"tile": p, "score": round(float(s), 4), "angle": round(float(a), 1)}
                for s, a, p in picked]
