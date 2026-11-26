# -*- coding: utf-8 -*-
"""布阵 → 兵种搭配推荐（clashlab.strategy）的契约测试。"""
import json
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _strong_layout(th_tile=(22, 22)):
    """中心大本营 + 9 座 X 连弩：对空/对地 100%，无明确可打弱点。"""
    bs = [{"type": "town-hall", "tile": list(th_tile)}]
    for x, y in ((8, 8), (8, 22), (8, 36), (22, 8), (22, 22),
                 (22, 36), (36, 8), (36, 22), (36, 36)):
        bs.append({"type": "x-bow", "tile": [x, y]})
    return {"name": "strong", "grid": 44, "buildings": bs, "walls": []}


def _air_gap_layout():
    """纯对地防御：对空 0%，应触发空军优先。"""
    return {"name": "airgap", "grid": 44, "buildings": [
        {"type": "town-hall", "tile": [22, 22]},
        {"type": "cannon", "tile": [18, 18]},
        {"type": "mortar", "tile": [26, 26]},
        {"type": "bomb-tower", "tile": [18, 26]},
    ], "walls": []}


def _th_bias_layout():
    """大本营贴左上角 + 满覆盖防御：应触发英雄切入。"""
    lay = _strong_layout(th_tile=(4, 4))
    lay["name"] = "thbias"
    return lay


def _compartment_layout():
    """6 个闭合隔间（各关一座 X 连弩）+ 中心大本营：应触发地面强拆。"""
    walls, bs = [], [{"type": "town-hall", "tile": [22, 22]}]
    for ox, oy in ((4, 4), (4, 16), (4, 28), (16, 4), (16, 16), (16, 28)):
        for x in range(ox, ox + 5):
            walls += [[x, oy], [x, oy + 4]]
        for y in range(oy, oy + 5):
            walls += [[ox, y], [ox + 4, y]]
        bs.append({"type": "x-bow", "tile": [ox + 2, oy + 2]})
    bs.append({"type": "x-bow", "tile": [26, 22]})
    return {"name": "compartments", "grid": 44, "buildings": bs, "walls": walls}


class TestGeneral(unittest.TestCase):
    def test_empty_layout_returns_general(self):
        from clashlab.strategy import recommend
        for lay in ({}, {"name": "empty", "grid": 44, "buildings": [], "walls": []}, None):
            recs = recommend(lay)
            self.assertTrue(recs, "空布局也要给通用推荐")
            self.assertEqual(recs[0]["reason"], "general")
            self.assertIn(recs[0]["archetype"], ("air", "ground", "hero-dive", "hybrid"))

    def test_no_weakness_returns_general(self):
        from clashlab.strategy import recommend
        recs = recommend(_strong_layout(), th=16)
        self.assertTrue(recs)
        self.assertEqual(recs[0]["reason"], "general")
        self.assertEqual(recs[0]["archetype"], "hybrid")


class TestFeatureDriven(unittest.TestCase):
    def test_air_gap_triggers_air_first(self):
        from clashlab.strategy import recommend
        recs = recommend(_air_gap_layout(), th=16)
        self.assertTrue(recs)
        self.assertEqual(recs[0]["archetype"], "air")
        self.assertEqual(recs[0]["reason"], "air-gap")
        self.assertIn("对空", recs[0]["why"])

    def test_town_hall_bias_triggers_hero_dive(self):
        from clashlab.strategy import recommend
        recs = recommend(_th_bias_layout(), th=16)
        self.assertTrue(recs)
        self.assertEqual(recs[0]["archetype"], "hero-dive")
        self.assertEqual(recs[0]["reason"], "th-bias")
        self.assertIn("大本营", recs[0]["why"])

    def test_many_compartments_trigger_ground(self):
        from clashlab.strategy import recommend
        recs = recommend(_compartment_layout(), th=16)
        self.assertTrue(recs)
        self.assertEqual(recs[0]["archetype"], "ground")
        self.assertEqual(recs[0]["reason"], "compartment-density")
        self.assertIn("隔间", recs[0]["why"])


class TestThAndSchema(unittest.TestCase):
    def test_th_parameter_effective(self):
        from clashlab.strategy import recommend
        lay = _air_gap_layout()
        r13 = recommend(lay, th=13)
        r16 = recommend(lay, th=16)
        self.assertTrue(r13 and r16)
        self.assertTrue(all(r["th"] == 13 for r in r13))
        self.assertTrue(all(r["th"] == 16 for r in r16))
        self.assertTrue(all("TH13" in v["url"] for v in r13[0]["videos"]))
        self.assertNotEqual(r13[0]["troops"], r16[0]["troops"], "TH 参数应改变数量模板")

    def test_recommend_accepts_layout_path(self):
        from clashlab.strategy import recommend, detect_signals
        p = os.path.join(ROOT, "bases", "th16", "03", "layout.json")
        recs = recommend(p, th=16)
        self.assertTrue(recs)
        self.assertEqual(recs[0]["th"], 16)
        reason, signals = detect_signals(p)
        self.assertIn(reason, ("air-gap", "th-bias", "compartment-density", "general"))
        self.assertTrue(signals)

    def test_videos_are_search_links_only(self):
        from clashlab.strategy import recommend, YOUTUBE_SEARCH
        for th in (13, 16, 19):
            for rec in recommend(_air_gap_layout(), th=th):
                self.assertTrue(1 <= len(rec["videos"]) <= 3)
                for v in rec["videos"]:
                    self.assertTrue(v["url"].startswith(YOUTUBE_SEARCH), v["url"])
                    self.assertTrue(v["title"].startswith("YouTube 搜索："))
                    q = v["url"][len(YOUTUBE_SEARCH):]
                    self.assertTrue(q.strip(), "搜索词不能为空")
                    for bad in ("watch?v=", "youtu.be/", "/embed/", "/shorts/"):
                        self.assertNotIn(bad, v["url"])

    def test_recommendation_schema_complete(self):
        from clashlab.strategy import recommend
        for rec in recommend(_air_gap_layout(), th=16):
            for key in ("archetype", "troops", "why", "steps", "videos",
                        "reason", "th", "name", "source", "confidence"):
                self.assertIn(key, rec)
            self.assertIn(rec["archetype"], ("air", "ground", "hero-dive", "hybrid"))
            self.assertIsInstance(rec["troops"], dict)
            self.assertTrue(rec["troops"])
            for k, n in rec["troops"].items():
                self.assertIsInstance(k, str)
                self.assertIsInstance(n, int)
                self.assertGreater(n, 0)
            self.assertIsInstance(rec["why"], str)
            self.assertGreaterEqual(len(rec["why"]), 8)
            self.assertTrue(3 <= len(rec["steps"]) <= 5, rec["steps"])
            self.assertTrue(0.0 < float(rec["confidence"]) <= 1.0)
            self.assertTrue(rec["source"])

    def test_deterministic_same_input_same_output(self):
        from clashlab.strategy import recommend
        a = recommend(_air_gap_layout(), th=16)
        b = recommend(_air_gap_layout(), th=16)
        self.assertEqual(json.dumps(a, ensure_ascii=False, sort_keys=True),
                         json.dumps(b, ensure_ascii=False, sort_keys=True))


class TestDataAndCli(unittest.TestCase):
    def test_knowledge_data_coverage(self):
        from clashlab.strategy import load_strategies, load_hero_equipment
        data = load_strategies()
        strategies = data["strategies"]
        self.assertGreaterEqual(len(strategies), 12)
        for s in strategies:
            self.assertTrue(s.get("source"))
            self.assertTrue(0 < float(s.get("confidence", 0)) <= 1)
            self.assertTrue(3 <= len(s.get("steps", [])) <= 5)
            self.assertTrue(1 <= len(s.get("video_queries", [])) <= 3)
            for th in range(13, 20):
                self.assertIn(str(th), s["troops_by_th"], s["id"])
        eq = load_hero_equipment()
        self.assertIn("参考", eq.get("disclaimer", ""))
        for th in range(13, 20):
            self.assertIn(str(th), eq["recommendations"])

    def test_cli_json_and_human(self):
        layout = os.path.join(ROOT, "bases", "th16", "03", "layout.json")
        base = [sys.executable, os.path.join(ROOT, "tools", "strategy_cli.py"),
                "--layout", layout, "--th", "16"]
        p = subprocess.run(base + ["--json"], cwd=ROOT, capture_output=True,
                           text=True, encoding="utf-8", timeout=120)
        self.assertEqual(p.returncode, 0, p.stderr)
        payload = json.loads(p.stdout)
        self.assertEqual(payload["th"], 16)
        self.assertTrue(payload["recommendations"])
        self.assertTrue(payload["signals"])
        for rec in payload["recommendations"]:
            self.assertTrue(rec["videos"])
            self.assertTrue(all(v["url"].startswith("https://www.youtube.com/results?search_query=")
                                for v in rec["videos"]))
        h = subprocess.run(base, cwd=ROOT, capture_output=True,
                           text=True, encoding="utf-8", timeout=120)
        self.assertEqual(h.returncode, 0, h.stderr)
        self.assertIn("推荐", h.stdout)
        self.assertIn("YouTube 搜索", h.stdout)


if __name__ == "__main__":
    unittest.main()
