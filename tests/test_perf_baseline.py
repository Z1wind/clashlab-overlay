# -*- coding: utf-8 -*-
"""test_perf_baseline.py —— 性能基线（只记录数字、不判死）。

被测版本快照（详见 tests/README.md）：
  clashlab/overlay/tactics.py mtime 2026-11-24 14:35:09
    sha256 758F854B73F3A8441333DA54A12BD0EE1FCCA1EF36035751F4284FE4EADBA6CC
  clashlab/knowledge.py      mtime 2026-11-24 13:39:31
    sha256 1BF3745AD70FDE02501E24E2DEA61F78061AD5A73B7BD9ECA06B357971AA78BE

基线：load_local <5ms（缓存稳态）、parse_plan_marks <5ms、retrieve <50ms。
超阈值只打印实测中位数并记录，**不判死**（机器负载波动不构成失败）。
全部临时数据造，不碰真实 out/ 与 knowledge/tactics。
"""
import json
import os
import statistics
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from clashlab import knowledge
from clashlab.overlay import tactics

RUNS = 21
RESULTS = {}


def _median_ms(fn, runs=RUNS):
    samples = []
    for _ in range(runs):
        t0 = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - t0) * 1000.0)
    return statistics.median(samples), min(samples), max(samples)


class TestPerfBaseline(unittest.TestCase):
    def setUp(self):
        # --- load_local 稳态：临时根 + info.json，先预热缓存再测 ---
        self.local_root = tempfile.mkdtemp(prefix="clashlab_perf_local_")
        os.makedirs(os.path.join(self.local_root, "out", "prebattle"))
        info = {
            "th": 14,
            "exposed": [
                {"type": "air-defense", "tile": [15, 30], "dps": 300, "edge_dist": 3},
                {"type": "wizard-tower", "tile": [25, 12], "dps": 240, "edge_dist": 5},
            ],
            "blind": [], "defense_counts": {},
            "core_cover_dps": None, "centroid": None, "layout_id": "x",
        }
        with open(os.path.join(self.local_root, "out", "prebattle", "info.json"),
                  "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False)
        tactics.load_local(self.local_root, th=14)  # 预热

        # --- retrieve：临时小卡库，先预热 load_cards 缓存 ---
        self.kb_dir = tempfile.mkdtemp(prefix="clashlab_perf_kb_")
        for i in range(8):
            card = {
                "id": f"p{i}", "th": 14, "army": ["edrag"],
                "pattern": "edrag_rush" if i % 2 == 0 else "hybrid",
                "confidence": 0.7,
                "source": {"title": f"战术卡{i}", "site": "test", "url": ""},
                "key_points": [f"要点{i}"],
            }
            with open(os.path.join(self.kb_dir, f"p{i}.json"), "w",
                      encoding="utf-8") as f:
                json.dump(card, f, ensure_ascii=False)
        knowledge.load_cards(self.kb_dir)  # 预热

        self.plan_text = (
            "【威胁排序】鹰炮 格(36,9)；防空塔 格(15,30)；法师塔 格(25,12)。\n"
            "【进攻路线】防空塔 格(15,30) → 法师塔 格(25,12) → 大本营 格(20,20)。\n"
            "【兵种与法术】本地规则建议：先清边铺主力，具体配比待联网模型复核。\n"
        )

    def test_load_local_baseline(self):
        median, lo, hi = _median_ms(
            lambda: tactics.load_local(self.local_root, th=14))
        RESULTS["load_local"] = (median, lo, hi, 5.0)
        print(f"\n[perf] load_local 中位数 {median:.3f}ms "
              f"(区间 {lo:.3f}-{hi:.3f}ms) 基线 5ms —— 仅记录不判死")

    def test_parse_plan_marks_baseline(self):
        median, lo, hi = _median_ms(
            lambda: tactics.parse_plan_marks({"text": self.plan_text}))
        RESULTS["parse_plan_marks"] = (median, lo, hi, 5.0)
        print(f"\n[perf] parse_plan_marks 中位数 {median:.3f}ms "
              f"(区间 {lo:.3f}-{hi:.3f}ms) 基线 5ms —— 仅记录不判死")

    def test_retrieve_baseline(self):
        brief = {"th": 14, "army": ["edrag"], "pattern": "edrag_rush"}
        median, lo, hi = _median_ms(
            lambda: knowledge.retrieve(brief=brief, k=3, dir=self.kb_dir))
        RESULTS["retrieve"] = (median, lo, hi, 50.0)
        print(f"\n[perf] retrieve 中位数 {median:.3f}ms "
              f"(区间 {lo:.3f}-{hi:.3f}ms) 基线 50ms —— 仅记录不判死")

    @classmethod
    def tearDownClass(cls):
        print("\n===== 性能基线汇总（超阈值仅记录，不判死） =====")
        for name, (median, lo, hi, base) in sorted(RESULTS.items()):
            flag = "OK" if median <= base else f"超基线 {median - base:.3f}ms"
            print(f"  {name}: {median:.3f}ms (min {lo:.3f} / max {hi:.3f}) "
                  f"基线 {base}ms -> {flag}")


if __name__ == "__main__":
    unittest.main()
