# -*- coding: utf-8 -*-
"""研究页「推荐」行 + prebattle 策略接线测试。"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

LAYOUT = os.path.join(ROOT, "bases", "th16", "03", "layout.json")


class TestFmtStrategy(unittest.TestCase):
    def test_summary_preferred(self):
        try:
            from clashlab.overlay.pages import _fmt_strategy_info
        except Exception as e:
            self.skipTest("pages 依赖不可用：%r" % (e,))
        self.assertEqual(_fmt_strategy_info({"strategy_summary": "电龙平推（air-gap）"}),
                         "推荐：电龙平推（air-gap）")

    def test_fallback_to_first_rec(self):
        from clashlab.overlay.pages import _fmt_strategy_info
        line = _fmt_strategy_info({"strategies": [{"name": "女武神强拆", "reason": "compartment-density"}]})
        self.assertEqual(line, "推荐：女武神强拆（compartment-density）")

    def test_empty_is_no_data(self):
        from clashlab.overlay.pages import _fmt_strategy_info
        self.assertEqual(_fmt_strategy_info({}), "推荐：无数据")
        self.assertEqual(_fmt_strategy_info(None), "推荐：无数据")


class TestPrebattleStrategies(unittest.TestCase):
    def test_collect_info_has_strategies(self):
        from clashlab import prebattle
        info = prebattle.collect_info(layout=LAYOUT)
        recs = info.get("strategies")
        self.assertIsInstance(recs, list)
        self.assertGreaterEqual(len(recs), 1)
        for r in recs:
            for k in ("name", "reason", "archetype", "troops", "steps", "videos"):
                self.assertIn(k, r)
        self.assertTrue(info.get("strategy_summary"))


if __name__ == "__main__":
    unittest.main()
