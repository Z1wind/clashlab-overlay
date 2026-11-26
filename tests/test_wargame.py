# -*- coding: utf-8 -*-
"""赛前兵棋推演引擎（clashlab/wargame.py）的契约测试。

覆盖：
  1. 单防御对单部队的伤害结算（防御按射程打最近部队，部队先死）
  2. 单部队对单建筑的伤害结算（建筑血量清空即摧毁）
  3. 墙阻挡：部队被墙挡住时先拆墙，拆穿前打不到建筑
  4. 同 seed 确定性：两次 run() 结果逐字节一致
  5. Monte Carlo 统计范围合法 + timeline 有序
  6. 建筑被摧毁计数（2 栋打掉 1 栋 => 50%）
  7. 未知兵种给出可读报错

全部为纯函数测试，不依赖 ImGui / 窗口 / 抓屏 / cv2。
"""
import json
import os
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

LAYOUT_03 = os.path.join(_ROOT, "bases", "th16", "03", "layout.json")


def _layout(grid=20, buildings=None, walls=None, name="synthetic"):
    return {"name": name, "grid": grid, "buildings": buildings or [], "walls": walls or []}


def _b(type_, tile, **over):
    d = {"type": type_, "tile": list(tile)}
    d.update(over)
    return d


def _wall_col(x, y0, y1):
    return [[x, y] for y in range(y0, y1 + 1)]


class TestWargameContracts(unittest.TestCase):
    def test_01_single_defense_kills_unit(self):
        """一个高 dps 防御在射程内应先把单部队打死，且建筑不掉血。"""
        from clashlab import wargame

        lay = _layout(buildings=[_b("cannon", (10, 10), hp=5000, dps=1000, range=15)])
        res = wargame.simulate_once(lay, {"archer": 1}, spawn=(2, 10), max_time=5.0, tick=0.5)
        self.assertEqual(res["units_alive"], 0, "部队应被防御击杀")
        self.assertEqual(res["buildings_destroyed"], 0, "部队没碰到建筑，建筑不该被摧毁")
        self.assertEqual(res["destruction"], 0.0)
        self.assertAlmostEqual(res["events"][-1]["t"], res["time"], places=6)
        self.assertEqual(res["events"][-1]["event"], "end")

    def test_02_single_unit_destroys_building(self):
        """单部队对无防御建筑：血量清空即摧毁，摧毁率 100%。"""
        from clashlab import wargame

        lay = _layout(buildings=[_b("cannon", (10, 10), hp=100, dps=0, range=0)])
        res = wargame.simulate_once(lay, {"barbarian": 1}, spawn=(8, 10), max_time=4.0, tick=0.5)
        self.assertEqual(res["buildings_destroyed"], 1)
        self.assertEqual(res["buildings_total"], 1)
        self.assertEqual(res["destruction"], 100.0)
        self.assertEqual(res["hp_destroyed"], 100.0)
        kinds = [e["event"] for e in res["events"]]
        self.assertIn("building_destroyed", kinds)

    def test_03_wall_blocks_then_breaks(self):
        """墙挡住去路：部队先对墙造成伤害；拆穿后才打得到建筑。"""
        from clashlab import wargame

        bld = [_b("cannon", (9, 10), hp=100, dps=0, range=0)]
        walled = _layout(buildings=bld, walls=_wall_col(5, 5, 14))
        open_ = _layout(buildings=bld, walls=[])

        # 1.5s 内：墙只被啃掉一部分，建筑应毫发无损
        r1 = wargame.simulate_once(walled, {"giant": 1}, spawn=(4, 10),
                                   max_time=1.5, tick=0.5, wall_hp=300)
        self.assertGreater(r1["walls"]["total"], 0)
        # 注意：hp_remaining 是全部墙格的总和（10 格 × 300），不是单格血量
        self.assertLess(r1["walls"]["hp_remaining"], r1["walls"]["total"] * 300.0,
                        "被墙挡住时应攻击墙体")
        self.assertEqual(r1["buildings_destroyed"], 0, "墙没拆穿前打不到建筑")

        # 同样的墙策略放宽到 10s：墙必被拆穿，建筑最终被摧毁
        r2 = wargame.simulate_once(walled, {"giant": 1}, spawn=(4, 10),
                                   max_time=10.0, tick=0.5, wall_hp=300)
        self.assertEqual(r2["buildings_destroyed"], 1, "墙拆穿后应摧毁建筑")

        # 无墙对照组：同样 6s 内应已摧毁
        r3 = wargame.simulate_once(open_, {"giant": 1}, spawn=(4, 10),
                                   max_time=6.0, tick=0.5, wall_hp=300)
        self.assertEqual(r3["buildings_destroyed"], 1, "无墙时部队应直接打到建筑")

    def test_04_same_seed_is_deterministic(self):
        """同 layout / army / trials / seed 两次 run 必须完全一致。"""
        from clashlab import wargame

        army = {"giant": 8, "wizard": 8}
        a = wargame.run(LAYOUT_03, army, trials=6, seed=7)
        b = wargame.run(LAYOUT_03, army, trials=6, seed=7)
        self.assertEqual(json.dumps(a, ensure_ascii=False, sort_keys=True),
                         json.dumps(b, ensure_ascii=False, sort_keys=True))
        self.assertEqual(a["trials"], 6)
        self.assertEqual(a["army"], army)

    def test_05_mc_stats_and_timeline_valid(self):
        """N 次统计范围合法，best.spawn 落在网格内，timeline 按时间非降序。"""
        from clashlab import wargame

        res = wargame.run(LAYOUT_03, {"giant": 5, "wizard": 10, "earthquake": 2},
                          trials=10, seed=3)
        d = res["destruction"]
        for k in ("mean", "p10", "p90", "min", "max"):
            self.assertIn(k, d)
            self.assertTrue(0.0 <= d[k] <= 100.0, "%s 越界: %r" % (k, d[k]))
        self.assertLessEqual(d["min"], d["p10"])
        self.assertLessEqual(d["p10"], d["mean"])
        self.assertLessEqual(d["mean"], d["p90"])
        self.assertLessEqual(d["p90"], d["max"])

        n = res["grid"]
        x, y = res["best"]["spawn"]
        self.assertTrue(0 <= x < n and 0 <= y < n, "best.spawn 越界: %r" % (res["best"]["spawn"],))
        self.assertTrue(0.0 <= res["best"]["destruction"] <= 100.0)

        self.assertIsInstance(res["timeline"], list)
        self.assertGreater(len(res["timeline"]), 0, "timeline 不应为空")
        ts = [e["t"] for e in res["timeline"]]
        self.assertEqual(ts, sorted(ts), "timeline 必须按时间非降序")

    def test_06_building_destroyed_count(self):
        """2 栋建筑只打掉 1 栋：destroyed=1 / destruction=50%。"""
        from clashlab import wargame

        lay = _layout(buildings=[
            _b("cannon", (10, 10), hp=100, dps=0, range=0),
            _b("town-hall", (18, 18), hp=100000, dps=0, range=0),
        ])
        res = wargame.simulate_once(lay, {"barbarian": 1}, spawn=(8, 10), max_time=5.0, tick=0.5)
        self.assertEqual(res["buildings_total"], 2)
        self.assertEqual(res["buildings_destroyed"], 1)
        self.assertEqual(res["destruction"], 50.0)

    def test_07_unknown_unit_rejected(self):
        """未知兵种要报可读错误（列出可用兵种），而不是静默忽略。"""
        from clashlab import wargame

        with self.assertRaises(ValueError) as ctx:
            wargame.run(LAYOUT_03, {"dragon-z": 3}, trials=1, seed=1)
        msg = str(ctx.exception)
        self.assertIn("dragon-z", msg)
        self.assertIn("giant", msg)


if __name__ == "__main__":
    unittest.main(verbosity=2)
