# -*- coding: utf-8 -*-
"""全大本营数据层（clashlab/th_data.py）的契约测试。

覆盖：
  1. TH16 数值与既有 assets.STATS / assets.TH16_OVERRIDE 完全一致（不回归）
  2. TH19 可查（hp/dps/range/size/level + source/confidence）
  3. 缺失回退：不高于该 TH 的最近档 + approx=True + approx_from
  4. 未知建筑走 DEFAULT_FALLBACK 兜底，并标记 unknown
  5. supported_town_halls() 覆盖 1..19
  6. 网格尺寸一致：所有档 grid=44、town-hall=4x4
  7. TH17–19 解锁列表与 reviewed ruleset 对齐
  8. assets.stats(name, th) 委托 th_data，且 th=None 旧语义不变
  9. TH17–19 的 size/level 取自 reviewed ruleset（精确），hp/dps 为低置信外推
 10. 每档元数据都带 source / confidence / status
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from clashlab import assets, th_data  # noqa: E402

NUM_KEYS = ("hp", "dps", "range", "level")


class TestTh16Unchanged(unittest.TestCase):
    def test_01_th16_numbers_match_existing_tables(self):
        """TH16 数值必须与 STATS / TH16_OVERRIDE 逐项相等（不回归）。"""
        for name, base in assets.STATS.items():
            got = th_data.stats(name, 16)
            for key in NUM_KEYS + ("size",):
                if key in base:
                    self.assertEqual(got.get(key), base[key],
                                     "TH16 %s.%s 被改动：%r != %r" % (name, key, got.get(key), base[key]))
        for name, over in assets.TH16_OVERRIDE.items():
            got = th_data.stats(name, 16)
            for key in NUM_KEYS:
                if key in over:
                    self.assertEqual(got.get(key), over[key],
                                     "TH16 %s.%s 被改动：%r != %r" % (name, key, got.get(key), over[key]))

    def test_02_th16_is_not_marked_approx(self):
        st = th_data.stats("monolith", 16)
        self.assertFalse(st["approx"])
        self.assertIsNone(st["approx_from"])
        self.assertEqual(st["th"], 16)


class TestTh19Queryable(unittest.TestCase):
    def test_03_th19_stats_available(self):
        st = th_data.stats("monolith", 19)
        self.assertEqual(st["th"], 19)
        self.assertFalse(st["approx"])
        self.assertGreater(st["hp"], 0)
        self.assertGreater(st["dps"], 0)
        self.assertEqual(st["size"], 3)
        self.assertEqual(st["level"], 5)          # reviewed: monolith TH19 = Lv5
        self.assertIn(st["confidence"], ("high", "medium", "low"))
        self.assertTrue(st["source"])

    def test_04_th19_new_defenses_are_unlocked(self):
        meta = th_data.town_hall_meta(19)
        for name in ("spiky-tower", "firecracker-tower", "guardian-shrine",
                     "revenge-tower", "super-wizard-tower", "firespitter"):
            self.assertIn(name, meta["unlocked"], "TH19 应解锁 %s" % name)


class TestFallback(unittest.TestCase):
    def test_05_missing_falls_back_to_nearest_lower(self):
        st = th_data.stats("x-bow", 15)
        self.assertTrue(st["approx"])
        self.assertEqual(st["approx_from"], 13)
        self.assertEqual(st["hp"], assets.STATS["x-bow"]["hp"])
        self.assertEqual(st["dps"], assets.STATS["x-bow"]["dps"])

    def test_06_unknown_building_uses_default_fallback(self):
        st = th_data.stats("ghost-tower", 16)
        self.assertTrue(st["approx"])
        self.assertTrue(st["unknown"])
        for key in ("hp", "dps", "range"):
            self.assertEqual(st[key], assets.DEFAULT_FALLBACK[key])
        self.assertEqual(st["confidence"], "low")


class TestCoverage(unittest.TestCase):
    def test_07_supported_town_halls_covers_1_to_19(self):
        self.assertEqual(list(th_data.supported_town_halls()), list(range(1, 20)))
        self.assertEqual(tuple(th_data.SUPPORTED_TOWN_HALLS), tuple(range(1, 20)))

    def test_08_grid_consistent_across_all_town_halls(self):
        for th in th_data.supported_town_halls():
            meta = th_data.town_hall_meta(th)
            self.assertEqual(meta["grid"], 44, "TH%d grid" % th)
            self.assertEqual(meta["town_hall_size"], 4, "TH%d town-hall 尺寸" % th)
            self.assertEqual(th_data.stats("town-hall", th)["size"], 4, "TH%d town-hall size" % th)

    def test_09_unlock_lists_follow_reviewed_ruleset(self):
        self.assertNotIn("firespitter", th_data.town_hall_meta(16)["unlocked"])
        self.assertIn("firespitter", th_data.town_hall_meta(17)["unlocked"])
        self.assertNotIn("multi-gear-tower", th_data.town_hall_meta(16)["unlocked"])
        self.assertIn("multi-gear-tower", th_data.town_hall_meta(17)["unlocked"])
        self.assertNotIn("revenge-tower", th_data.town_hall_meta(17)["unlocked"])
        self.assertIn("revenge-tower", th_data.town_hall_meta(18)["unlocked"])
        self.assertIn("spiky-tower", th_data.town_hall_meta(19)["unlocked"])
        self.assertNotIn("spiky-tower", th_data.town_hall_meta(18)["unlocked"])
        for th in (1, 8, 13, 19):
            self.assertIn("cannon", th_data.town_hall_meta(th)["unlocked"])
            self.assertIn("town-hall", th_data.town_hall_meta(th)["unlocked"])

    def test_10_meta_carries_source_and_confidence(self):
        for th in th_data.supported_town_halls():
            meta = th_data.town_hall_meta(th)
            self.assertIn(meta["status"], ("exact", "approx", "unverified"))
            self.assertTrue(meta["source"])
            self.assertIn(meta["confidence"], ("high", "medium", "low"))


class TestReviewedSizesAndLevels(unittest.TestCase):
    def test_11_th17_19_sizes_from_ruleset(self):
        self.assertEqual(th_data.stats("eagle-artillery", 17)["size"], 4)
        self.assertEqual(th_data.stats("inferno-tower", 19)["size"], 2)
        self.assertEqual(th_data.stats("clan-castle", 18)["size"], 3)
        self.assertEqual(th_data.stats("spiky-tower", 19)["size"], 3)

    def test_12_th17_19_levels_from_ruleset(self):
        cases = {("air-defense", 17): 15, ("air-defense", 18): 16, ("air-defense", 19): 17,
                 ("cannon", 17): 21, ("clan-castle", 19): 15, ("firespitter", 18): 3}
        for (name, th), want in cases.items():
            self.assertEqual(th_data.stats(name, th)["level"], want, "%s@TH%d" % (name, th))

    def test_13_th17_19_hp_dps_are_low_confidence_estimates(self):
        for th in (17, 18, 19):
            st = th_data.stats("cannon", th)
            self.assertEqual(st["confidence"], "low", "TH%d cannon 应标低置信" % th)
            self.assertTrue(st.get("note"), "TH%d cannon 应说明外推口径" % th)


class TestAssetsDelegation(unittest.TestCase):
    def test_14_assets_stats_delegates(self):
        a = assets.stats("monolith", 19)
        b = th_data.stats("monolith", 19)
        for key in NUM_KEYS:
            self.assertEqual(a[key], b[key])
        self.assertEqual(assets.stats("x-bow", 15)["approx_from"], 13)

    def test_15_assets_stats_none_keeps_old_semantics(self):
        st = assets.stats("cannon")
        self.assertEqual(st, assets.STATS["cannon"])
        self.assertNotIn("approx", st)
        self.assertEqual(assets.stats("ghost-tower"), assets.DEFAULT_FALLBACK)


if __name__ == "__main__":
    unittest.main()
