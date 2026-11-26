# -*- coding: utf-8 -*-
"""英雄落点 → 穿云箭方向 & 落点敏感性。

    python tools/arrow_placement_cli.py --layout out/annotate/01_annotated.json --queen 20,20
    python tools/arrow_placement_cli.py --layout ... --queen 20,20 --radius 0.6 --step 0.2
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
from clashlab.overlay import arrow_placement as ap  # noqa: E402


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--layout", required=True)
    a.add_argument("--queen", required=True, help="英雄落点 tile，如 20,20")
    a.add_argument("--grid", type=int, default=44)
    a.add_argument("--tol", type=float, default=1.2)
    a.add_argument("--radius", type=float, default=0.5)
    a.add_argument("--step", type=float, default=0.25)
    a.add_argument("--corner", action="store_true", help="tile 是左上角坐标（默认按中心）")
    a.add_argument("--emit-overlay", action="store_true", help="写 config/giant_arrow_overlay.json")
    args = a.parse_args()
    lay = json.load(open(args.layout, encoding="utf-8"))
    qx, qy = [float(x) for x in args.queen.split(",")]
    mode = "corner" if args.corner else "center"
    res = ap.arrow_from_placement(lay, [qx, qy], grid=args.grid, tol=args.tol, center_mode=mode)
    tgt = res.get("target")
    print("落点 (%g,%g) -> 最近目标: %s 中心(%s) 距离 %s 格" % (
        qx, qy, tgt["type"] if tgt else "无", tgt["center"] if tgt else "-",
        tgt["dist"] if tgt else "-"))
    print("箭线方向: %s°  from %s -> %s" % (res.get("angle_deg"), res.get("from"), res.get("to")))
    print("命中: %s" % res.get("summary"))
    for i, h in enumerate(res.get("hits") or [], 1):
        print("  %d. %-14s 格(%s) 偏 %.2f" % (i, h["type"], h["tile"], h["perp"]))
    sens = ap.placement_sensitivity(lay, [qx, qy], radius=args.radius, step=args.step,
                                    grid=args.grid, tol=args.tol, center_mode=mode)
    print("\n落点敏感性：样本 %d，不同结果 %d，目标翻转 %d，稳定=%s" % (
        sens["samples"], sens["distinct_signatures"], sens["flips"], sens["stable"]))
    for v in sens["variants"][:8]:
        print("  offset %s -> %s %s hits=%d" % (v["offset"], v["target"], v["angle_deg"], len(v["hits"])))
    if args.emit_overlay and res.get("to"):
        out = os.path.join(ROOT, "config", "giant_arrow_overlay.json")
        payload = {"from": res["from"], "to": res["to"],
                   "hits": [{"type": h["type"], "tile": h["tile"], "order": h["order"],
                             "perp": h["perp"]} for h in res.get("hits") or []],
                   "summary": res["summary"], "score": res["score"],
                   "queen": [qx, qy], "stable": sens["stable"]}
        os.makedirs(os.path.dirname(out), exist_ok=True)
        json.dump(payload, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("已写 HUD overlay 计划:", out)


if __name__ == "__main__":
    main()
