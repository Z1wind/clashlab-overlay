# -*- coding: utf-8 -*-
"""批量阵型测试：真实标注阵变体 + 生成阵，跑穿云箭自动选线 + 落点敏感性。

输出 out/arrow_batch/report.json 与终端汇总表。不伪造真实战图：API 的布局接口 401。
"""
import glob
import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from clashlab.overlay import giant_arrow_diagram as ga
from clashlab.overlay import arrow_placement as ap

OUT = os.path.join(ROOT, "out", "arrow_batch")
os.makedirs(OUT, exist_ok=True)
GRID = 44


def load_real():
    out = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "out", "annotate", "*_annotated.json"))):
        lay = json.load(open(f, encoding="utf-8"))
        out[os.path.basename(f).replace("_annotated.json", "") + "-ann"] = lay
    for f in sorted(glob.glob(os.path.join(ROOT, "bases", "th16", "*", "layout.json"))):
        lay = json.load(open(f, encoding="utf-8"))
        out[os.path.basename(os.path.dirname(f)) + "-base"] = lay
    f = os.path.join(ROOT, "layouts", "th13_sample.json")
    if os.path.exists(f):
        out["th13-sample"] = json.load(open(f, encoding="utf-8"))
    return out


def transform(lay, mode):
    b = [dict(x) for x in lay.get("buildings") or []]
    walls = [[int(p[0]), int(p[1])] for p in (lay.get("walls") or []) if isinstance(p, (list, tuple))]
    def tx(x, y):
        if mode == "mirror":
            return GRID - x, y
        if mode == "rot90":
            return y, GRID - x
        if mode == "diag":
            return GRID - y, GRID - x
        return x, y
    for x in b:
        x["tile"] = list(tx(float(x["tile"][0]), float(x["tile"][1])))
    walls = [list(tx(float(p[0]), float(p[1]))) for p in walls]
    return {"name": (lay.get("name") or "x") + "-" + mode, "grid": GRID, "buildings": b, "walls": walls}


def make_synth(seed):
    rng = random.Random(seed)
    types = ["air-defense", "air-sweeper", "hidden-tesla", "cannon", "archer-tower", "x-bow",
             "inferno-tower", "scattershot", "monolith", "eagle-artillery", "wiz-tower"] * 2
    used = set()
    bs = []
    for t in types[:26]:
        for _ in range(60):
            x = rng.randint(3, GRID - 4)
            y = rng.randint(3, GRID - 4)
            if all(abs(x - ux) > 2 or abs(y - uy) > 2 for ux, uy in used):
                used.add((x, y))
                bs.append({"type": t, "tile": [x, y]})
                break
    return {"name": "synth-%02d" % seed, "grid": GRID, "buildings": bs, "walls": []}


def pick_queen(lay):
    air = [b for b in lay.get("buildings") or [] if b.get("type") in ("air-sweeper", "air-defense")]
    if not air:
        return [3.0, 3.0]
    t = air[0]["tile"]
    # 从地图边缘找一个离该对空目标最近的落点
    cands = []
    for x in range(1, 43):
        for y in (1, 43):
            cands.append((x, y))
    for y in range(1, 43):
        for x in (1, 43):
            cands.append((x, y))
    best = min(cands, key=lambda p: abs(p[0] - t[0]) + abs(p[1] - t[1]))
    return [float(best[0]), float(best[1])]


def run_case(name, lay):
    opt = ga.optimize_giant_arrow(lay, top=3)
    best = opt.get("best")
    queen = pick_queen(lay)
    res = ap.arrow_from_placement(lay, queen)
    sens = ap.placement_sensitivity(lay, queen, radius=0.5, step=0.25)
    return {
        "name": name, "buildings": len(lay.get("buildings") or []),
        "best_score": (best or {}).get("score"),
        "best_summary": (best or {}).get("summary"),
        "queen": queen, "queen_target": (res.get("target") or {}).get("type"),
        "queen_angle": res.get("angle_deg"),
        "queen_hits": res.get("summary"),
        "stable": sens["stable"], "distinct": sens["distinct_signatures"], "flips": sens["flips"],
    }


def main():
    layouts = {}
    for name, lay in load_real().items():
        for mode in ("orig", "mirror", "rot90", "diag"):
            layouts[name + "-" + mode] = lay if mode == "orig" else transform(lay, mode)
    for i in range(10):
        layouts["synth-%02d" % i] = make_synth(1000 + i)
    rows = [run_case(n, l) for n, l in layouts.items()]
    json.dump({"cases": rows, "n": len(rows)}, open(os.path.join(OUT, "report.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    stable = sum(1 for r in rows if r["stable"])
    flips = sum(1 for r in rows if r["flips"])
    print("cases:", len(rows), "| 落点稳定:", stable, "| 出现目标翻转:", flips)
    print("%-22s %5s %5s %6s %6s %8s %6s %4s" % ("case", "blds", "hits", "sweep", "ad", "stable", "dist", "flip"))
    for r in rows:
        s = r["best_summary"] or {}
        print("%-22s %5d %5d %6d %6d %8s %6d %4d" % (
            r["name"][:22], r["buildings"], sum(1 for _ in (s or {}).get("air_total") and []),  # noqa
            s.get("air_sweeper", 0), s.get("air_defense", 0),
            r["stable"], r["distinct"], r["flips"]))
    print("report:", os.path.join(OUT, "report.json"))


if __name__ == "__main__":
    main()
