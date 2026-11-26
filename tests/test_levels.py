# -*- coding: utf-8 -*-
"""levels 缩放曲线测试。"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestLevels(unittest.TestCase):
    def test_full_level_is_one(self):
        from clashlab import levels
        for fn, mx in ((levels.building_scale, 20), (levels.troop_scale, 11), (levels.hero_scale, 95)):
            sc = fn(mx) if fn is levels.hero_scale else fn(mx, mx)
            v = sc if isinstance(sc, float) else sc["hp"]
            self.assertAlmostEqual(v, 1.0, places=6)

    def test_monotonic(self):
        from clashlab import levels
        a = levels.building_scale(5, 20)["hp"]
        b = levels.building_scale(10, 20)["hp"]
        c = levels.building_scale(20, 20)["hp"]
        self.assertLess(a, b)
        self.assertLess(b, c)
        self.assertLess(levels.troop_scale(3)["dps"], levels.troop_scale(9)["dps"])
        self.assertLess(levels.hero_scale(10), levels.hero_scale(60))

    def test_clamped(self):
        from clashlab import levels
        self.assertAlmostEqual(levels.building_scale(999, 20)["hp"], 1.0, places=6)
        self.assertAlmostEqual(levels.building_scale(-3, 20)["hp"],
                               levels.building_scale(1, 20)["hp"], places=6)

    def test_hero_army_boost_bounds(self):
        from clashlab import levels
        self.assertAlmostEqual(levels.army_boost({}), 1.0)
        low = levels.army_boost({"queen": 5, "king": 5})
        high = levels.army_boost({"queen": 95, "king": 95})
        self.assertGreater(low, 0.5)
        self.assertLess(low, high)
        self.assertLessEqual(high, 1.0000001)

    def test_max_level_of_building(self):
        from clashlab import levels
        lv = levels.max_level_of("cannon", 16)
        self.assertGreater(lv, 10)
        self.assertEqual(levels.max_level_of("ghost-tower", 16), levels.DEFAULT_MAX_LEVEL)

    def test_building_scale_is_deterministic(self):
        from clashlab import levels
        a = levels.building_scale(9, 21)
        b = levels.building_scale(9, 21)
        self.assertEqual(a, b)


class TestThDataLevelIntegration(unittest.TestCase):
    def test_level_scales_hp_dps(self):
        from clashlab import th_data
        base = th_data.stats("cannon", 16)
        low = th_data.stats("cannon", 16, level=5)
        self.assertLess(low["hp"], base["hp"])
        self.assertLess(low["dps"], base["dps"])
        self.assertEqual(low["level"], 5)
        self.assertFalse(low["level_estimated"])

    def test_max_level_keeps_baseline(self):
        from clashlab import th_data
        base = th_data.stats("cannon", 16)
        mx = int(base.get("level") or 0)
        top = th_data.stats("cannon", 16, level=mx)
        self.assertAlmostEqual(top["hp"], base["hp"], places=3)
        self.assertAlmostEqual(top["dps"], base["dps"], places=3)

    def test_no_level_is_estimated(self):
        from clashlab import th_data
        self.assertTrue(th_data.stats("cannon", 16)["level_estimated"])

