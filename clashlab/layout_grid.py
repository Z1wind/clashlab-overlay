# -*- coding: utf-8 -*-
"""布局网格层：把 annotated JSON（墙=折线/点，建筑=tile）规范成 44×44 逐格模型，
并给出可验证的墙体/隔间指标。供规则评分与校验复用。"""
from __future__ import annotations
import math

N = 44
WALL = "#"
EMPTY = "."
BUILDING = "B"


def _is_point(v):
    return isinstance(v, (list, tuple)) and len(v) >= 2 and not isinstance(v[0], (list, tuple))


def _segments_to_polyline(points):
    """平铺点列表可能是「折线」也可能是「两两配对的线段端点」，用平均段长判断。"""
    if len(points) < 4:
        return points
    consec = [math.hypot(points[i + 1][0] - points[i][0], points[i + 1][1] - points[i][1])
              for i in range(len(points) - 1)]
    pairs = [math.hypot(points[i + 1][0] - points[i][0], points[i + 1][1] - points[i][1])
             for i in range(0, len(points) - 1, 2)]
    avg_consec = sum(consec) / max(1, len(consec))
    avg_pair = sum(pairs) / max(1, len(pairs))
    if len(points) % 2 == 0 and avg_pair > avg_consec * 1.8 and avg_pair >= 3.0:
        # 端点配对：展开成 起点->终点->起点... 的折线（彼此不相连也无妨，栅格采样按段处理）
        flat = []
        for i in range(0, len(points) - 1, 2):
            flat.append(points[i]); flat.append(points[i + 1])
        return flat
    return points


def _polyline_points(walls):
    """兼容多种墙表示：[[x,y],...] 折线 / 两两线段端点 / {'points': [...]} / tile 列表。"""
    pts = []
    for w in walls or []:
        if isinstance(w, dict):
            seq = w.get("points") or w.get("polyline") or w.get("tiles") or []
            pts.extend(_flatten(seq))
        elif _is_point(w):
            pts.append((float(w[0]), float(w[1])))
        elif isinstance(w, (list, tuple)):
            pts.extend(_flatten(w))
    return _segments_to_polyline(pts)


def _flatten(seq):
    out = []
    for p in seq or []:
        if _is_point(p):
            out.append((float(p[0]), float(p[1])))
    return out


class LayoutGrid:
    """44×44 栅格：每个 tile 记录 wall / building。"""

    def __init__(self, n=N):
        self.n = n
        self.walls = set()
        self.buildings = {}

    @classmethod
    def from_layout(cls, lay: dict, n=N):
        g = cls(n)
        g._rasterize_walls(lay.get("walls") or [])
        for b in lay.get("buildings") or []:
            t = b.get("tile") or [0, 0]
            x, y = int(round(float(t[0]))), int(round(float(t[1])))
            if 0 <= x < n and 0 <= y < n:
                g.buildings[(x, y)] = b.get("type") or "unknown"
        return g

    def _rasterize_walls(self, walls):
        pts = _polyline_points(walls)
        if not pts:
            return
        if len(pts) == 1:
            self._mark_wall(pts[0])
            return
        # 折线：相邻点间按 0.25 tile 步长密集采样
        for i in range(len(pts) - 1):
            x0, y0 = pts[i]; x1, y1 = pts[i + 1]
            steps = max(1, int(math.hypot(x1 - x0, y1 - y0) / 0.25))
            for s in range(steps + 1):
                f = s / steps
                self._mark_wall((x0 + (x1 - x0) * f, y0 + (y1 - y0) * f))

    def _mark_wall(self, p):
        x, y = int(math.floor(p[0])), int(math.floor(p[1]))
        if 0 <= x < self.n and 0 <= y < self.n:
            self.walls.add((x, y))

    # ---------------- 指标 ----------------
    def wall_count(self):
        return len(self.walls)

    def building_count(self):
        return len(self.buildings)

    def compartments(self, min_tiles=4):
        """墙围出的闭合区域：从无墙格出发 flood fill，未触边且面积≥min_tiles 即隔间。"""
        open_tiles = {(x, y) for x in range(self.n) for y in range(self.n) if (x, y) not in self.walls}
        seen = set(); comps = []
        for start in open_tiles:
            if start in seen:
                continue
            stack = [start]; seen.add(start); tiles = []; touch_edge = False
            while stack:
                x, y = stack.pop(); tiles.append((x, y))
                if x in (0, self.n - 1) or y in (0, self.n - 1):
                    touch_edge = True
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nb = (x + dx, y + dy)
                    if nb in open_tiles and nb not in seen:
                        seen.add(nb); stack.append(nb)
            if not touch_edge and len(tiles) >= min_tiles:
                comps.append(tiles)
        return comps

    def wall_efficiency(self):
        """孤立墙段比例：四邻无墙的格数 / 总墙数。"""
        if not self.walls:
            return 0.0
        iso = sum(1 for (x, y) in self.walls
                  if not any((x + dx, y + dy) in self.walls for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))))
        return iso / len(self.walls)

    def th_inside_walls(self):
        """大本是否被墙围住：要么位于闭合隔间内，要么四邻墙 >=2。"""
        th = [pos for pos, t in self.buildings.items() if t == "town-hall"]
        if not th:
            return False
        comps = self.compartments(min_tiles=4)
        for pos in th:
            if any(pos in c for c in comps):
                return True
            x, y = pos
            ring = [(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)]
            if sum(1 for p in ring if p in self.walls) >= 2:
                return True
        return False

    def validate(self):
        """结构校验：越界/重叠/墙压在建筑上。返回问题列表。"""
        issues = []
        for (x, y) in self.buildings:
            if (x, y) in self.walls:
                issues.append({"kind": "wall-over-building", "tile": [x, y]})
        for (x, y) in list(self.walls) + list(self.buildings):
            if not (0 <= x < self.n and 0 <= y < self.n):
                issues.append({"kind": "out-of-bounds", "tile": [x, y]})
        return issues
