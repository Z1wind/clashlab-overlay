# -*- coding: utf-8 -*-
"""非防御建筑（经济/兵营）不应被当防御。"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LAY = {"name": "t", "grid": 20,
       "buildings": [{"type": "town-hall", "tile": [9, 9], "level": 16},
                     {"type": "cannon", "tile": [3, 3], "level": 21},
                     {"type": "gold-mine", "tile": [16, 16], "level": 17},
                     {"type": "army-camp", "tile": [4, 16], "level": 14}],
       "walls": []}


class TestEconomyNotDefense(unittest.TestCase):
    def test_economy_dps_zero(self):
        from clashlab import wargame
        L = wargame.parse_layout(LAY)
        by = {b["type"]: b for b in L.buildings}
        self.assertEqual(by["gold-mine"]["dps"], 0.0)
        self.assertEqual(by["army-camp"]["dps"], 0.0)
        self.assertGreater(by["cannon"]["dps"], 0.0)

    def test_economy_size_from_ruleset(self):
        from clashlab import wargame
        L = wargame.parse_layout(LAY)
        by = {b["type"]: b for b in L.buildings}
        self.assertGreaterEqual(by["gold-mine"]["size"], 3)

    def test_sim_still_runs(self):
        from clashlab import wargame
        r = wargame.simulate_once(LAY, {"giant": 4}, spawn=(1, 9), seed=1)
        self.assertGreaterEqual(r["destruction"], 0)


if __name__ == "__main__":
    unittest.main()
