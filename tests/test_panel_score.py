# -*- coding: utf-8 -*-
"""P3b-1 评分接入 PANEL 的 RED 测试（纯函数，不依赖 ImGui）。"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _layout(with_walls=False):
    lay = {"name": "t", "grid": 44,
           "buildings": [{"type": "town-hall", "tile": [21, 21]},
                         {"type": "air-defense", "tile": [17, 17]},
                         {"type": "cannon", "tile": [25, 25]},
                         {"type": "archer-tower", "tile": [18, 25]}],
           "walls": []}
    if with_walls:
        lay["walls"] = [[x, 14] for x in range(14, 30)] + [[x, 30] for x in range(14, 30)]
    return lay


class TestScoreCard(unittest.TestCase):
    def test_missing_layout_unavailable(self):
        from clashlab.overlay import score_card
        card = score_card.card_from_layout(None)
        self.assertFalse(card["available"])
        self.assertEqual(score_card.status_suffix(card), "")
        self.assertEqual(score_card.bottom_text(card), "")
        empty = score_card.card_from_layout({"name": "x", "grid": 44, "buildings": [], "walls": []})
        self.assertFalse(empty["available"])

    def test_card_values_and_texts(self):
        from clashlab.overlay import score_card
        card = score_card.card_from_layout(_layout())
        self.assertTrue(card["available"])
        self.assertGreaterEqual(card["overall"], 0.0)
        self.assertLessEqual(card["overall"], 100.0)
        self.assertIn(card["grade"], list("SABCDF"))
        self.assertIn("评分", score_card.status_suffix(card))
        self.assertIn(card["grade"], score_card.bottom_text(card))
        self.assertLessEqual(len(card["top"]), 2)

    def test_detail_lines(self):
        from clashlab.overlay import score_card
        lay = _layout()
        lay["buildings"] = [{"type": "town-hall", "tile": [4, 4]},
                            {"type": "cannon", "tile": [25, 25]},
                            {"type": "mortar", "tile": [17, 27]}]
        lines = score_card.detail_lines(lay)
        self.assertTrue(1 <= len(lines) <= 2)
        self.assertTrue(any("大本营" in x or "对空" in x or "对地" in x for x in lines))
        self.assertEqual(score_card.detail_lines(None), [])

    def test_cache_returns_same_card_object(self):
        from clashlab.overlay import score_card
        score_card.reset_cache()
        lay = _layout()
        a = score_card.card_from_layout(lay)
        b = score_card.card_from_layout(lay)
        self.assertIs(a, b)
        # 换布局后重新算
        lay2 = _layout(with_walls=True)
        c = score_card.card_from_layout(lay2)
        self.assertIsNot(a, c)


if __name__ == "__main__":
    unittest.main()
