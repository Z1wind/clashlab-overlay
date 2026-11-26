# -*- coding: utf-8 -*-
"""wargame 等级输入测试：建筑等级 / 兵种等级 / 英雄等级。"""
import copy
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_LAYOUT = {"name": "t16", "grid": 20,
               "buildings": [{"type": "town-hall", "tile": [9, 9]},
                             {"type": "cannon", "tile": [4, 4]},
                             {"type": "archer-tower", "tile": [15, 15]}],
               "walls": []}


def _layout(level=None):
    lay = copy.deepcopy(BASE_LAYOUT)
    if level is not None:
        for b in lay["buildings"]:
            if b["type"] != "town-hall":
                b["level"] = level
    return lay


class TestWargameLevels(unittest.TestCase):
    def test_low_level_base_easier(self):
        from clashlab import wargame
        army = {"giant": 4, "wizard": 6}
        low = wargame.simulate_once(_layout(2), army, spawn=(2, 10), seed=3)
        high = wargame.simulate_once(_layout(20), army, spawn=(2, 10), seed=3)
        self.assertGreaterEqual(low["buildings_destroyed"], high["buildings_destroyed"])

    def test_troop_levels_monotonic(self):
        from clashlab import wargame
        lay = _layout(None)
        low = wargame.simulate_once(lay, {"giant": 4, "wizard": 6}, spawn=(2, 10), seed=3,
                                    troop_levels={"giant": 2, "wizard": 2})
        high = wargame.simulate_once(lay, {"giant": 4, "wizard": 6}, spawn=(2, 10), seed=3,
                                     troop_levels={"giant": 11, "wizard": 11})
        self.assertGreaterEqual(high["destruction"], low["destruction"])

    def test_hero_levels_boost(self):
        from clashlab import wargame
        lay = _layout(None)
        low = wargame.simulate_once(lay, {"giant": 4}, spawn=(2, 10), seed=3,
                                    hero_levels={"queen": 5})
        high = wargame.simulate_once(lay, {"giant": 4}, spawn=(2, 10), seed=3,
                                     hero_levels={"queen": 95})
        self.assertGreater(high["destruction"], low["destruction"])

    def test_no_levels_matches_baseline(self):
        from clashlab import wargame
        lay = _layout(None)
        a = wargame.simulate_once(lay, {"giant": 3}, spawn=(2, 10), seed=1)
        b = wargame.simulate_once(lay, {"giant": 3}, spawn=(2, 10), seed=1,
                                  troop_levels=None, hero_levels=None)
        self.assertEqual(a["destruction"], b["destruction"])

    def test_deterministic_with_levels(self):
        from clashlab import wargame
        kw = dict(spawn=(2, 10), seed=5, troop_levels={"giant": 7},
                  hero_levels={"king": 40})
        a = wargame.simulate_once(_layout(8), {"giant": 4}, **kw)
        b = wargame.simulate_once(_layout(8), {"giant": 4}, **kw)
        self.assertEqual(a, b)

    def test_run_passes_levels(self):
        from clashlab import wargame
        lay = _layout(6)
        out = wargame.run(lay, {"giant": 2}, trials=2, seed=1,
                          troop_levels={"giant": 5}, hero_levels={"queen": 20})
        self.assertIn("destruction", out)
        self.assertGreaterEqual(out["destruction"]["mean"], 0)


if __name__ == "__main__":
    unittest.main()
