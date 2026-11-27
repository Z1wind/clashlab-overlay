# -*- coding: utf-8 -*-
import unittest
from clashlab.battle_sim import simulate

ARMY = {"miner": 21, "hog-rider": 11, "healer": 4}

class T(unittest.TestCase):
    def test_open_base_runs(self):
        lay = {"buildings": [{"type": "town-hall", "tile": [20, 20]},
                             {"type": "cannon", "tile": [18, 20]}], "walls": []}
        r = simulate(lay, ARMY)
        self.assertTrue(r["ok"])
        self.assertEqual(r["walls_to_break"], 0)
        self.assertGreater(r["path_len"], 5)
        self.assertIn(r["stars_estimate"], (1, 2, 3))

    def test_walls_increase_cost(self):
        open_lay = {"buildings": [{"type": "town-hall", "tile": [20, 20]}], "walls": []}
        ring = []
        for x in range(10, 31):
            ring += [[x, 10], [x, 30]]
        for y in range(10, 31):
            ring += [[10, y], [30, y]]
        walled = {"buildings": [{"type": "town-hall", "tile": [20, 20]}], "walls": ring}
        a = simulate(open_lay, ARMY)
        b = simulate(walled, ARMY)
        self.assertTrue(b["ok"])
        self.assertGreaterEqual(b["walls_to_break"], 1)  # 闭合墙必须破墙进入
        self.assertGreater(b["path_cost"], a["path_cost"])

    def test_missing_th(self):
        r = simulate({"buildings": [{"type": "cannon", "tile": [5, 5]}], "walls": []}, ARMY)
        self.assertFalse(r["ok"])
        self.assertIn("大本", r["error"])

if __name__ == "__main__":
    unittest.main()
