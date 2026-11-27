# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "layout_grid.py")
t = open(p, encoding="utf-8").read()
old = '''    def th_inside_walls(self):
        for (x, y), t in self.buildings.items():
            if t == "town-hall":
                ring = [(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)]
                return sum(1 for p in ring if p in self.walls) >= 3
        return False'''
new = '''    def th_inside_walls(self):
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
        return False'''
if old in t:
    t = t.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("th_inside_walls fixed")
else:
    print("anchor miss")
