# -*- coding: utf-8 -*-
"""P3c-1 女王穿云箭战术图：纯函数 RED 测试（不建窗口、不抓屏、不发请求）。

被测契约（clashlab/overlay/giant_arrow_diagram.py）：
  giant_arrow_spec(plan) -> 从 schema v2 phases 里抽出第一个含 giant-arrow 单位的阶段
      {phase_index, index, name, t_start, t_end, from, to, route, targets, units, purpose}
      无 giant-arrow -> None
  match_skewered(layout, frm, to, tol=1.2) -> 被箭线「穿到」的建筑列表
      [{type, tile, t, perp, order}]，order 按沿箭线投影 t 升序从 1 编号
  render_giant_arrow_diagram(layout, plan, out_png, ...) -> PIL Image 并落盘
"""
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

PLAN = {
    "ok": True, "goal": "三星", "model": "deepseek-v4.1-flash",
    "win_condition": "先巨箭串掉三座防空",
    "phases": [
        {"i": 1, "name": "战前箭清", "t_start": 0, "t_end": 10,
         "units": [{"type": "giant-arrow", "count": 1, "drop_tile": [1, 27]}],
         "route": [[1, 27], [15, 21], [21, 19]],
         "targets": [[15, 21], [18, 21], [21, 19]],
         "purpose": "一箭串掉三座防空"},
        {"i": 2, "name": "西侧清边", "t_start": 10, "t_end": 50,
         "units": [{"type": "balloon", "count": 3, "drop_tile": [2, 36]}],
         "route": [[2, 36], [8, 33]], "targets": [[8, 33]], "purpose": "清边"},
    ],
    "threats": [],
}

LAYOUT = {"name": "synthetic", "grid": 44,
          "buildings": [
              {"type": "air-defense", "tile": [15, 21]},
              {"type": "air-defense", "tile": [18, 21]},
              {"type": "air-defense", "tile": [21, 19]},
              {"type": "cannon", "tile": [10, 24]},      # 箭线附近 0.56 格
              {"type": "mortar", "tile": [5, 5]},        # 离线很远
          ],
          "walls": []}


class TestGiantArrowSpec(unittest.TestCase):
    def test_extracts_first_giant_arrow_phase(self):
        from clashlab.overlay import giant_arrow_diagram as gad
        spec = gad.giant_arrow_spec(PLAN)
        self.assertIsNotNone(spec)
        self.assertEqual(spec["phase_index"], 0)
        self.assertEqual(spec["index"], 1)
        self.assertEqual(spec["name"], "战前箭清")
        self.assertEqual(spec["from"], [1.0, 27.0])
        self.assertEqual(spec["to"], [21.0, 19.0])
        self.assertEqual(len(spec["targets"]), 3)
        self.assertEqual((spec["t_start"], spec["t_end"]), (0.0, 10.0))

    def test_no_giant_arrow_returns_none(self):
        from clashlab.overlay import giant_arrow_diagram as gad
        p = {"phases": [{"i": 1, "name": "x", "units": [{"type": "edrag"}],
                         "route": [[1, 1], [2, 2]]}]}
        self.assertIsNone(gad.giant_arrow_spec(p))
        self.assertIsNone(gad.giant_arrow_spec({}))
        self.assertIsNone(gad.giant_arrow_spec(None))

    def test_from_falls_back_to_route_start(self):
        from clashlab.overlay import giant_arrow_diagram as gad
        p = {"phases": [{"i": 1, "name": "箭", "units": [{"type": "giant-arrow", "count": 1}],
                         "route": [[4, 5], [20, 20]], "targets": []}]}
        spec = gad.giant_arrow_spec(p)
        self.assertEqual(spec["from"], [4.0, 5.0])
        self.assertEqual(spec["to"], [20.0, 20.0])

    def test_to_falls_back_to_last_target(self):
        from clashlab.overlay import giant_arrow_diagram as gad
        p = {"phases": [{"i": 1, "name": "箭", "units": [{"type": "giant-arrow", "count": 1,
                                                          "drop_tile": [1, 1]}],
                         "route": [], "targets": [[10, 10], [12, 14]]}]}
        spec = gad.giant_arrow_spec(p)
        self.assertEqual(spec["from"], [1.0, 1.0])
        self.assertEqual(spec["to"], [12.0, 14.0])


class TestMatchSkewered(unittest.TestCase):
    def test_orders_along_arrow_and_prefers_tolerance(self):
        from clashlab.overlay import giant_arrow_diagram as gad
        hits = gad.match_skewered(LAYOUT, [1, 27], [21, 19], tol=1.2)
        tiles = [tuple(h["tile"]) for h in hits]
        # (10,24) t=0.44 < (15,21) 0.71 < (18,21) 0.84 < (21,19) 1.0
        self.assertEqual(tiles, [(10, 24), (15, 21), (18, 21), (21, 19)])
        self.assertEqual([h["order"] for h in hits], [1, 2, 3, 4])
        self.assertEqual(hits[0]["type"], "cannon")
        self.assertEqual(sum(1 for h in hits if h["type"] == "air-defense"), 3)

    def test_tolerance_excludes_far_buildings(self):
        from clashlab.overlay import giant_arrow_diagram as gad
        # 垂直距离：cannon(10,24)=0.557 格、AD(15,21)=0.371、AD(18,21)=0.743、AD(21,19)=0.0
        hits = gad.match_skewered(LAYOUT, [1, 27], [21, 19], tol=0.3)
        self.assertEqual([tuple(h["tile"]) for h in hits], [(21, 19)])
        hits2 = gad.match_skewered(LAYOUT, [1, 27], [21, 19], tol=0.6)
        self.assertEqual([tuple(h["tile"]) for h in hits2],
                         [(10, 24), (15, 21), (21, 19)])

    def test_empty_layout_is_empty_not_crash(self):
        from clashlab.overlay import giant_arrow_diagram as gad
        self.assertEqual(gad.match_skewered(None, [1, 1], [2, 2]), [])
        self.assertEqual(gad.match_skewered({"buildings": [], "walls": [[1, 1]]},
                                           [1, 1], [2, 2]), [])
        self.assertEqual(gad.match_skewered(LAYOUT, [5, 5], [5, 5]), [])


class TestRealDatasets(unittest.TestCase):
    """真实产物：bases/th16/03/layout.json + out/overlay/_plan_viz/plan_03_llm.json。"""

    @classmethod
    def setUpClass(cls):
        plan_path = os.path.join(ROOT, "out", "overlay", "_plan_viz", "plan_03_llm.json")
        if not os.path.exists(plan_path):
            raise unittest.SkipTest("需要本地 out/overlay/_plan_viz/plan_03_llm.json（不入库）")
        cls.layout = json.load(open(os.path.join(ROOT, "bases", "th16", "03", "layout.json"),
                                    encoding="utf-8"))
        cls.plan = json.load(open(plan_path, encoding="utf-8"))

    def test_real_spec_and_three_air_defenses(self):
        from clashlab.overlay import giant_arrow_diagram as gad
        spec = gad.giant_arrow_spec(self.plan)
        self.assertEqual(spec["from"], [1.0, 27.0])
        self.assertEqual(spec["to"], [21.0, 19.0])
        hits = gad.match_skewered(self.layout, spec["from"], spec["to"], tol=1.2)
        self.assertEqual([tuple(h["tile"]) for h in hits],
                         [(15, 21), (18, 21), (21, 19)])
        self.assertTrue(all(h["type"] == "air-defense" for h in hits))


class TestRenderIntegration(unittest.TestCase):
    def test_render_writes_png_and_returns_image(self):
        from clashlab.overlay import giant_arrow_diagram as gad
        tmp = tempfile.mkdtemp(prefix="p3c_arrow_")
        out = os.path.join(tmp, "arrow.png")
        im = gad.render_giant_arrow_diagram(LAYOUT, PLAN, out, title="测试穿云箭")
        self.assertTrue(os.path.exists(out))
        self.assertGreater(os.path.getsize(out), 5000)
        self.assertEqual(im.size, (1280, 1000))
        self.assertEqual(ImageSizeOf(out), (1280, 1000))

    def test_render_without_giant_arrow_does_not_crash(self):
        from clashlab.overlay import giant_arrow_diagram as gad
        tmp = tempfile.mkdtemp(prefix="p3c_arrow_no_")
        out = os.path.join(tmp, "noga.png")
        plan = {"phases": [{"i": 1, "name": "普攻", "units": [], "route": [[1, 1], [2, 2]]}]}
        im = gad.render_giant_arrow_diagram(LAYOUT, plan, out, title="无箭")
        self.assertEqual(im.size, (1280, 1000))
        self.assertTrue(os.path.exists(out))


def ImageSizeOf(path):
    from PIL import Image
    with Image.open(path) as im:
        return im.size


if __name__ == "__main__":
    unittest.main()
