# -*- coding: utf-8 -*-
import unittest
from types import SimpleNamespace
from clashlab.overlay.pages import _battle_sim_line

GOOD = {"buildings": [{"type": "town-hall", "tile": [20, 20]},
                      {"type": "air-defense", "tile": [18, 18]},
                      {"type": "cannon", "tile": [22, 22]}], "walls": []}

class T(unittest.TestCase):
    def test_no_layout(self):
        self.assertIn("无阵型", _battle_sim_line(SimpleNamespace(layout=None)))

    def test_sim_line(self):
        line = _battle_sim_line(SimpleNamespace(layout=GOOD))
        self.assertIn("模拟", line)
        self.assertIn("★", line)

    def test_cache_same_line(self):
        a = _battle_sim_line(SimpleNamespace(layout=GOOD))
        b = _battle_sim_line(SimpleNamespace(layout=GOOD))
        self.assertEqual(a, b)

if __name__ == "__main__":
    unittest.main()
