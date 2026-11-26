# -*- coding: utf-8 -*-
"""放兵线/区域优化 CLI。

    python tools/deploy_cli.py --layout bases/th16/03/layout.json --army '{"giant":10,"wizard":12}' --mode line --trials 12
"""
import argparse
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from clashlab import deploy  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="放兵点 -> 放兵线/区域 优化（提高摧毁率）")
    ap.add_argument("--layout", required=True)
    ap.add_argument("--army", required=True)
    ap.add_argument("--mode", default="line", choices=["point", "line", "region", "all"])
    ap.add_argument("--trials", type=int, default=10)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    army = json.loads(a.army)
    res = deploy.optimize(a.layout, army, mode=a.mode, trials=a.trials, seed=a.seed)
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return
    print("模式：%s，trials=%d，点基线=%.2f%%，最佳=%s %.2f%%（提升 %+.2f）" % (
        res["mode"], res["trials"], res["point_baseline"] or 0,
        res["best"]["id"], res["best"]["mean"], res["gain_vs_point"] or 0))
    for r in res["candidates"]:
        print("  %-14s %-6s mean=%5.2f%%  p10=%5.2f  p90=%5.2f  points=%s" % (
            r["id"], r["kind"], r["mean"], r["p10"], r["p90"], r["points"]))


if __name__ == "__main__":
    main()
