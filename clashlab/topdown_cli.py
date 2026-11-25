# -*- coding: utf-8 -*-
"""CLI：layout.json -> 2D 俯视 PNG + 2D 交换 JSON。

用法：
    python -m clashlab.topdown --layout bases/th16/03/layout.json --out out/overlay/_2d
"""
import argparse
import os
import sys

from .topdown import render_topdown, export_2d_json


def main(argv=None):
    ap = argparse.ArgumentParser(description="layout.json -> 2D top-down PNG / 2D JSON")
    ap.add_argument("--layout", required=True)
    ap.add_argument("--out", default="out/overlay/_2d")
    ap.add_argument("--cell", type=int, default=24)
    a = ap.parse_args(argv)
    import json
    lay = json.load(open(a.layout, encoding="utf-8"))
    os.makedirs(a.out, exist_ok=True)
    name = os.path.splitext(os.path.basename(a.layout))[0]
    parent = os.path.basename(os.path.dirname(os.path.abspath(a.layout)))
    base = parent if parent else name
    w, h, nb, nw = render_topdown(lay, os.path.join(a.out, base + "_topdown.png"), cell=a.cell)
    export_2d_json(lay, os.path.join(a.out, base + "_2d.json"))
    print("2D ok: %dx%d px, buildings=%d walls=%d -> %s" % (w, h, nb, nw, a.out))


if __name__ == "__main__":
    main()
