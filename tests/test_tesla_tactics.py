# -*- coding: utf-8 -*-
"""特斯拉隐身提醒 + 战术知识库测试。"""
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


class TestTeslaWarning(unittest.TestCase):
    def test_warning_when_tesla_present(self):
        from clashlab.overlay import giant_arrow_diagram as g
        lay = {"buildings": [{"type": "hidden-tesla", "tile": [10, 10]}]}
        warn = g.tesla_warning(lay)
        self.assertIn("特斯拉", warn)
        self.assertIn("不现形", warn)
        self.assertIn("DPS", warn)

    def test_no_warning_without_tesla(self):
        from clashlab.overlay import giant_arrow_diagram as g
        self.assertEqual(g.tesla_warning({"buildings": [{"type": "cannon", "tile": [1, 1]}]}), "")

    def test_tesla_not_positive_score(self):
        from clashlab.overlay import giant_arrow_diagram as g
        self.assertLess(g.score_hits([{"type": "hidden-tesla"}]), 0)


class TestTacticsKnowledge(unittest.TestCase):
    def test_knowledge_schema(self):
        p = os.path.join(ROOT, "knowledge", "tactics.json")
        d = json.load(open(p, encoding="utf-8"))
        self.assertGreaterEqual(len(d.get("entries") or []), 4)
        for e in d["entries"]:
            for k in ("id", "topic", "fact", "source"):
                self.assertIn(k, e)
            self.assertTrue(e["fact"])

    def test_has_tesla_facts(self):
        p = os.path.join(ROOT, "knowledge", "tactics.json")
        d = json.load(open(p, encoding="utf-8"))
        ids = {e["id"] for e in d["entries"]}
        self.assertIn("hidden-tesla-invisible", ids)
        self.assertIn("hidden-tesla-low-value", ids)


if __name__ == "__main__":
    unittest.main()
