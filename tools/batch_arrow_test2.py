# -*- coding: utf-8 -*-
"""批量阵型压测 v2：真实标注阵 × 8 变体 + 20 生成阵，统计选线与落点稳定性。"""
import glob, json, os, random, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from clashlab.overlay import giant_arrow_diagram as ga
from clashlab.overlay import arrow_placement as ap
OUT = os.path.join(ROOT, "out", "arrow_batch"); os.makedirs(OUT, exist_ok=True)
GRID = 44

def load_real():
    out = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "out", "annotate", "*_annotated.json"))):
        out[os.path.basename(f).replace("_annotated.json", "") + "-ann"] = json.load(open(f, encoding="utf-8"))
    for f in sorted(glob.glob(os.path.join(ROOT, "bases", "th16", "*", "layout.json"))):
        out[os.path.basename(os.path.dirname(f)) + "-base"] = json.load(open(f, encoding="utf-8"))
    f = os.path.join(ROOT, "layouts", "th13_sample.json")
    if os.path.exists(f):
        out["th13-sample"] = json.load(open(f, encoding="utf-8"))
    return out

def transform(lay, mode):
    b = [dict(x) for x in lay.get("buildings") or []]
    walls = [[int(p[0]), int(p[1])] for p in (lay.get("walls") or []) if isinstance(p, (list, tuple))]
    def tx(x, y):
        if mode == "mirror": return GRID - x, y
        if mode == "rot90": return y, GRID - x
        if mode == "diag": return GRID - y, GRID - x
        if mode == "shift2": return x + 2, y + 2
        if mode == "shiftn2": return x - 2, y - 2
        return x, y
    for x in b: x["tile"] = list(tx(float(x["tile"][0]), float(x["tile"][1])))
    walls = [list(tx(float(p[0]), float(p[1]))) for p in walls]
    return {"name": (lay.get("name") or "x") + "-" + mode, "grid": GRID, "buildings": b, "walls": walls}

def make_synth(seed):
    rng = random.Random(seed)
    pool = ["air-defense", "air-sweeper", "hidden-tesla", "cannon", "archer-tower", "x-bow",
            "inferno-tower", "scattershot", "monolith", "eagle-artillery", "wizard-tower"] * 3
    used, bs = set(), []
    for t in pool[:26]:
        for _ in range(80):
            x, y = rng.randint(3, GRID - 4), rng.randint(3, GRID - 4)
            if all(abs(x - ux) > 2 or abs(y - uy) > 2 for ux, uy in used):
                used.add((x, y)); bs.append({"type": t, "tile": [x, y]}); break
    return {"name": "synth-%02d" % seed, "grid": GRID, "buildings": bs, "walls": []}

def pick_queen(lay):
    air = [b for b in lay.get("buildings") or [] if b.get("type") in ("air-sweeper", "air-defense")]
    t = air[0]["tile"] if air else [GRID // 2, GRID // 2]
    cands = [(x, y) for x in range(1, 43) for y in (1, 43)] + [(x, y) for y in range(1, 43) for x in (1, 43)]
    p = min(cands, key=lambda q: abs(q[0] - t[0]) + abs(q[1] - t[1]))
    return [float(p[0]), float(p[1])]

def main():
    layouts = {}
    for name, lay in load_real().items():
        for mode in ("orig", "mirror", "rot90", "diag", "shift2", "shiftn2"):
            layouts[name + "-" + mode] = lay if mode == "orig" else transform(lay, mode)
    for i in range(20):
        layouts["synth-%02d" % i] = make_synth(2000 + i)
    rows = []
    for name, lay in layouts.items():
        opt = ga.optimize_giant_arrow(lay, top=3)
        best = opt.get("best") or {}
        queen = pick_queen(lay)
        res = ap.arrow_from_placement(lay, queen)
        sens = ap.placement_sensitivity(lay, queen, radius=0.5, step=0.25)
        summ = best.get("summary") or {}
        rows.append({"name": name, "buildings": len(lay.get("buildings") or []),
                     "best_score": best.get("score"), "best_hits": len(best.get("hits") or []),
                     "best_sweeper": summ.get("air_sweeper", 0), "best_ad": summ.get("air_defense", 0),
                     "queen": queen, "queen_target": (res.get("target") or {}).get("type"),
                     "queen_angle": res.get("angle_deg"), "queen_hits": len(res.get("hits") or []),
                     "stable": sens["stable"], "distinct": sens["distinct_signatures"], "flips": sens["flips"]})
    json.dump({"cases": rows, "n": len(rows)}, open(os.path.join(OUT, "report.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    n = len(rows); stable = sum(1 for r in rows if r["stable"]); flip = sum(1 for r in rows if r["flips"])
    real = [r for r in rows if not r["name"].startswith("synth")]
    print("cases=%d  real=%d  synth=%d" % (n, len(real), n - len(real)))
    print("落点稳定: %d/%d (%.0f%%)  出现目标翻转: %d 例" % (stable, n, 100.0 * stable / n, flip))
    print("真实阵最优线含吹风机: %d/%d" % (sum(1 for r in real if r["best_sweeper"]), len(real)))
    print("%-26s %4s %5s %4s %4s %4s %5s %4s" % ("case", "blds", "score", "hits", "sweep", "ad", "stable", "flip"))
    for r in rows:
        print("%-26s %4d %5s %4d %4d %4d %5s %4d" % (r["name"][:26], r["buildings"],
              r["best_score"], r["best_hits"], r["best_sweeper"], r["best_ad"], r["stable"], r["flips"]))
    print("report:", os.path.join(OUT, "report.json"))

if __name__ == "__main__":
    main()
