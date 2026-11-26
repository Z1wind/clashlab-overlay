# -*- coding: utf-8 -*-
"""HUD 穿云箭图层测试：不依赖真窗口，用 FakeDL / FakeCalib 记录调用。"""
import json
import os
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class FakeDL:
    def __init__(self):
        self.calls = []

    def add_line(self, a, b, col, th):
        self.calls.append(("line", a.x, a.y, b.x, b.y, th))

    def add_circle(self, p, r, col, seg, th):
        self.calls.append(("circle", p.x, p.y, r))

    def add_circle_filled(self, p, r, col, seg=0):
        self.calls.append(("circle_filled", p.x, p.y, r))

    def add_text(self, p, col, text):
        self.calls.append(("text", p.x, p.y, text))

    def add_triangle_filled(self, a, b, c, col):
        self.calls.append(("tri", a.x, a.y))


class FakeCalib:
    def tile_to_px(self, gx, gy):
        return 100.0 + gx * 10.0, 50.0 + gy * 10.0


class TestGiantArrowHud(unittest.TestCase):
    def test_draw_counts_and_calls(self):
        from clashlab.overlay import giant_arrow_hud as g
        plan = {"from": [0, 0], "to": [3, 3],
                "hits": [{"type": "air-defense", "tile": [1, 1], "order": 1},
                         {"type": "air-sweeper", "tile": [2, 2], "order": 2}]}
        dl = FakeDL()
        n = g.draw_giant_arrow(dl, FakeCalib(), plan)
        self.assertEqual(n, 2)
        kinds = [c[0] for c in dl.calls]
        self.assertIn("line", kinds)
        self.assertIn("tri", kinds)
        self.assertGreaterEqual(kinds.count("circle"), 3)
        self.assertGreaterEqual(kinds.count("text"), 3)

    def test_bad_plan_returns_zero(self):
        from clashlab.overlay import giant_arrow_hud as g
        self.assertEqual(g.draw_giant_arrow(FakeDL(), FakeCalib(), {}), 0)
        self.assertEqual(g.draw_giant_arrow(FakeDL(), None, {"from": [0, 0], "to": [1, 1]}), 0)

    def test_load_overlay_plan_mtime_cache(self):
        from clashlab.overlay import giant_arrow_hud as g
        root = tempfile.mkdtemp()
        p = os.path.join(root, "config")
        os.makedirs(p)
        path = os.path.join(p, "giant_arrow_overlay.json")
        self.assertIsNone(g.load_overlay_plan(root))
        json.dump({"from": [0, 0], "to": [1, 1], "hits": []}, open(path, "w"))
        first = g.load_overlay_plan(root)
        self.assertEqual(first["to"], [1, 1])
        second = g.load_overlay_plan(root)
        self.assertIs(first, second)

    def test_hit_color(self):
        from clashlab.overlay import giant_arrow_hud as g
        self.assertEqual(g.hit_color("air-defense"), g.RED)
        self.assertEqual(g.hit_color("air-sweeper"), g.ORANGE)
        self.assertEqual(g.hit_color("hidden-tesla"), g.GREY)


if __name__ == "__main__":
    unittest.main()
