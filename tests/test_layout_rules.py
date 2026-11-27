# -*- coding: utf-8 -*-
import unittest
from clashlab.layout_rules import evaluate

def base(buildings, walls=None):
    return {"buildings": buildings, "walls": walls or []}

TH = {"type":"town-hall","tile":[20,20]}

class T(unittest.TestCase):
    def test_bad_layout_fails_critical(self):
        r = evaluate(base([TH]))
        self.assertLess(r["score"], 50)
        ids = [x["id"] for x in r["failed"]]
        self.assertIn("R3", ids)               # 防空规则仍然判失败
        self.assertIn("R1", r["skipped"])      # 墙数据不完整 -> R1 不判定

    def test_good_layout_scores_higher(self):
        good = base([
            TH, {"type":"air-defense","tile":[18,18]}, {"type":"air-defense","tile":[30,18]},
            {"type":"air-sweeper","tile":[20,10]}, {"type":"inferno-tower","tile":[15,15]},
            {"type":"x-bow","tile":[25,15]}, {"type":"scattershot","tile":[20,28]},
            {"type":"gold-storage","tile":[16,24]},
        ], walls=[[8,8],[34,8],[34,34],[8,34],[8,8]])
        r = evaluate(good)
        self.assertGreater(r["score"], 50)
        self.assertIn(r["grade"], ("A","B","C","S"))
        self.assertTrue(all("id" in x for x in r["rules"]))

    def test_rules_are_explainable(self):
        r = evaluate(base([TH]))
        for x in r["rules"]:
            self.assertIn("title", x); self.assertIn("severity", x)
            self.assertIn("passed", x); self.assertIn("evidence", x)
            if not x["passed"] and not x.get("skipped"):
                self.assertIsNotNone(x["recommendation"])

if __name__ == "__main__":
    unittest.main()
