# -*- coding: utf-8 -*-
"""P3c-3 2D 推演接入 PANEL 的 RED 测试（纯函数，不依赖 ImGui / 窗口 / 抓屏）。

被测契约：
  line_from_summary(summary) -> 一行中文文案
    - 无数据（None / 空 dict / available=False / 缺 tile 或缺 destroy_pct）-> 「推演：无数据」
    - 有数据 -> 「推演：预估摧毁 XX% · 最佳落点 (x,y)」，XX 为 0-100 整数
  summary_from_plans(plans) -> 从 analysis.candidate_plans 的 top1 抽摘要
    - top1 = plans[0]（候选已按 predicted 降序）；取 entries[0].tile 与 predicted_raw
  summary_from_layout(layout, builder=...) -> 带指纹缓存（同一 layout 只算一次）
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _plans(raw=0.23, tile=(11, 41), pid="A", name="单点强攻"):
    return [{"id": pid, "name": name, "predicted": 1.0, "predicted_raw": raw,
             "risk": "低", "exposure": 6127,
             "entries": [{"tile": list(tile), "troops": 7, "score": 0.23}],
             "path": {"steps": 15, "time_s": 10.0, "exposure": 6127}}]


class TestSimLine(unittest.TestCase):
    def test_none_is_no_data(self):
        from clashlab.overlay import sim_panel
        self.assertEqual(sim_panel.line_from_summary(None), "推演：无数据")

    def test_unavailable_is_no_data(self):
        from clashlab.overlay import sim_panel
        self.assertEqual(sim_panel.line_from_summary({}), "推演：无数据")
        self.assertEqual(sim_panel.line_from_summary({"available": False}), "推演：无数据")

    def test_available_line_format(self):
        from clashlab.overlay import sim_panel
        line = sim_panel.line_from_summary(
            {"available": True, "destroy_pct": 23, "tile": [11, 41]})
        self.assertEqual(line, "推演：预估摧毁 23% · 最佳落点 (11,41)")

    def test_pct_rounded_and_clamped(self):
        from clashlab.overlay import sim_panel
        self.assertIn("预估摧毁 0%", sim_panel.line_from_summary(
            {"available": True, "destroy_pct": -5, "tile": [0, 0]}))
        self.assertIn("预估摧毁 100%", sim_panel.line_from_summary(
            {"available": True, "destroy_pct": 187.4, "tile": [43, 43]}))
        self.assertIn("预估摧毁 24%", sim_panel.line_from_summary(
            {"available": True, "destroy_pct": 23.6, "tile": [7, 8]}))

    def test_missing_tile_or_pct_is_no_data(self):
        from clashlab.overlay import sim_panel
        self.assertEqual(sim_panel.line_from_summary({"available": True, "destroy_pct": 30}),
                         "推演：无数据")
        self.assertEqual(sim_panel.line_from_summary(
            {"available": True, "tile": [3, 4]}), "推演：无数据")


class TestSummaryFromPlans(unittest.TestCase):
    def test_top1_fields(self):
        from clashlab.overlay import sim_panel
        s = sim_panel.summary_from_plans(_plans())
        self.assertTrue(s["available"])
        self.assertEqual(s["id"], "A")
        self.assertEqual(list(s["tile"]), [11, 41])
        self.assertEqual(s["destroy_pct"], 23)
        self.assertTrue(s["line"].startswith("推演：预估摧毁 23%"))

    def test_empty_plans_unavailable(self):
        from clashlab.overlay import sim_panel
        self.assertFalse(sim_panel.summary_from_plans([])["available"])
        self.assertEqual(sim_panel.summary_from_plans(None)["line"], "推演：无数据")

    def test_no_layout_unavailable(self):
        from clashlab.overlay import sim_panel
        sim_panel.reset_cache()
        s = sim_panel.summary_from_layout(None)
        self.assertFalse(s["available"])
        self.assertEqual(sim_panel.line_from_summary(s), "推演：无数据")


class TestSummaryCache(unittest.TestCase):
    def _layout(self, n_walls=0):
        return {"name": "t", "grid": 44,
                "buildings": [{"type": "town-hall", "tile": [21, 21]},
                              {"type": "air-defense", "tile": [17, 17]},
                              {"type": "cannon", "tile": [25, 25]}],
                "walls": [[x, 14] for x in range(10, 10 + n_walls)]}

    def test_cache_builds_once_per_layout(self):
        from clashlab.overlay import sim_panel
        sim_panel.reset_cache()
        calls = []

        def fake_builder(layout, army=None):
            calls.append(1)
            return {"available": True, "destroy_pct": 42, "tile": [3, 4], "id": "A",
                    "name": "单点强攻", "line": "推演：预估摧毁 42% · 最佳落点 (3,4)"}

        lay = self._layout()
        a = sim_panel.summary_from_layout(lay, builder=fake_builder)
        b = sim_panel.summary_from_layout(lay, builder=fake_builder)
        self.assertIs(a, b, "同一 layout 必须命中缓存（不能每帧重算）")
        self.assertEqual(len(calls), 1)
        # 换布局（墙数变化 -> 指纹变化）必须重算
        c = sim_panel.summary_from_layout(self._layout(n_walls=5), builder=fake_builder)
        self.assertEqual(len(calls), 2)
        self.assertIsNot(a, c)

    def test_builder_exception_is_no_data_not_crash(self):
        from clashlab.overlay import sim_panel
        sim_panel.reset_cache()

        def boom(layout, army=None):
            raise RuntimeError("sim exploded")

        s = sim_panel.summary_from_layout(self._layout(), builder=boom)
        self.assertFalse(s["available"])
        self.assertEqual(s["line"], "推演：无数据")


if __name__ == "__main__":
    unittest.main()
