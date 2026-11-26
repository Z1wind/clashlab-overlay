# -*- coding: utf-8 -*-
"""实机测试中发现的问题：UI 文案、#TAG、同名歧义。"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestLiveRobustness(unittest.TestCase):
    def test_tag_extracted(self):
        from clashlab.ocr_screen import _parse_lines
        got = _parse_lines(["#RPGLCCGY9", "cHetzz", "Wrath of Kings"])
        self.assertEqual(got["tag"], "#RPGLCCGY9")
        self.assertEqual(got["name"], "cHetzz")

    def test_tag_only(self):
        from clashlab.ocr_screen import _parse_lines
        got = _parse_lines(["#2GCG9LQRQ"])
        self.assertEqual(got["tag"], "#2GCG9LQRQ")

    def test_resolve_ambiguous_flag(self):
        from clashlab import cocapi
        cocapi._search_player_best = lambda *a, **kw: {"name": "chetzz", "tag": "#LUY8UJQJ",
                                                       "th": 13, "clan": {"name": "The Revengers"}}
        cocapi._find_clan_with_member = lambda *a, **kw: (None, None, None)
        cocapi.search_player = lambda *a, **kw: [
            {"name": "chetzz", "tag": "#LUY8UJQJ", "th": 13, "clan": {"name": "The Revengers"}}]
        r = cocapi.resolve_opponent("chetzz", "Wrath of Kings", fresh=True)
        self.assertTrue(r.get("ambiguous"))
        self.assertIn("warning", r)

    def test_resolve_by_tag(self):
        from clashlab import cocapi
        cocapi.player_th = lambda tag, fresh=False: 15
        r = cocapi.resolve_by_tag("#ABCDEFGH", fresh=True)
        self.assertEqual(r["player"]["tag"], "#ABCDEFGH")
        self.assertEqual(r["player"]["th"], 15)


if __name__ == "__main__":
    unittest.main()
