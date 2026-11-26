# -*- coding: utf-8 -*-
"""穿云箭自动选线 CLI。

    python tools/giant_arrow_cli.py --layout bases/th16/03/layout.json --top 5
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
from clashlab.overlay import giant_arrow_diagram as g  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layout", required=True)
    ap.add_argument("--grid", type=int, default=44)
    ap.add_argument("--tol", type=float, default=1.2)
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--emit-overlay", action="store_true",
                    help="写 config/giant_arrow_overlay.json 供 HUD 直接画在游戏上")
    a = ap.parse_args()
    lay = json.load(open(a.layout, encoding="utf-8"))
    res = g.optimize_giant_arrow(lay, grid=a.grid, tol=a.tol, top=a.top)
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
        return
    best = res.get("best")
    if a.emit_overlay:
        import time as _t
        if not best:
            print("没有对空目标，无法生成 overlay 计划")
            return
        out = os.path.join(ROOT, "config", "giant_arrow_overlay.json")
        payload = {"from": best["from"], "to": best["to"],
                   "hits": [{"type": h["type"], "tile": h["tile"],
                             "order": h["order"], "perp": h["perp"]} for h in best["hits"]],
                   "summary": best["summary"], "score": best["score"],
                   "ts": _t.strftime("%Y-%m-%dT%H:%M:%S")}
        os.makedirs(os.path.dirname(out), exist_ok=True)
        import json as _json
        _json.dump(payload, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("已写 HUD overlay 计划:", out)
        return
    if not best:
        print("没有对空目标（吹风机/防空火箭），无法选线")
        return
    print("最佳箭线：%s -> %s  评分 %.1f" % (best["from"], best["to"], best["score"]))
    print("  命中 %s" % best["summary"])
    for i, h in enumerate(best["hits"], 1):
        mark = {"air-defense": "防空", "air-sweeper": "吹风机", "hidden-tesla": "特斯拉?"}.get(h["type"], h["type"])
        print("   %d. %s 格(%d,%d) 偏 %.2f" % (i, mark, h["tile"][0], h["tile"][1], h["perp"]))
    print("\n候选（top %d）：" % a.top)
    for c in res["candidates"]:
        s = c["summary"]
        print("  %-18s -> %-18s 分 %5.1f | 防空 %d 吹风机 %d 特斯拉 %d 其它 %d" % (
            str(c["from"]), str(c["to"]), c["score"], s["air_defense"], s["air_sweeper"],
            s["tesla_hidden"], s["other"]))


if __name__ == "__main__":
    main()
