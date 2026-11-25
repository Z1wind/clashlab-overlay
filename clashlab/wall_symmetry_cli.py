# -*- coding: utf-8 -*-
"""CLI：按建筑对称补全墙线，并报告主城墙/独立墙段。

    python -m clashlab.wall_symmetry_cli --layout bases/th16/03/layout.json --out out/walls
"""
import argparse
import json
import os

from .wall_symmetry import apply_symmetry, main_walls, independent_walls


def main(argv=None):
    ap = argparse.ArgumentParser(description="infer/complement walls by symmetry")
    ap.add_argument("--layout", required=True)
    ap.add_argument("--out", default="out/walls")
    ap.add_argument("--min-overlap", type=float, default=0.5)
    a = ap.parse_args(argv)
    lay = json.load(open(a.layout, encoding="utf-8"))
    out = apply_symmetry(lay, min_overlap=a.min_overlap)
    os.makedirs(a.out, exist_ok=True)
    name = os.path.basename(os.path.dirname(os.path.abspath(a.layout)))
    path = os.path.join(a.out, name + "_walls.json")
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    info = out["meta"]["wall_symmetry"]
    mw = len(main_walls(out.get("walls") or []))
    iw = len(independent_walls(out.get("walls") or []))
    print("symmetry=%s score=%.2f walls %d -> %d (+%d) | main=%d independent=%d -> %s" % (
        info["symmetry"], info["score"], info["original"], info["completed"],
        info["inferred_count"], mw, iw, path))


if __name__ == "__main__":
    main()
