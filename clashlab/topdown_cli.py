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
    ap.add_argument("--layout", default=None)
    ap.add_argument("--annotated", default=None, help="标注文件（out/annotate/NN_annotated.json）")
    ap.add_argument("--out", default="out/overlay/_2d")
    ap.add_argument("--cell", type=int, default=24)
    a = ap.parse_args(argv)
    import json
    src = a.annotated or a.layout
    if not src:
        raise SystemExit("需要 --layout 或 --annotated")
    lay = json.load(open(src, encoding="utf-8"))
    os.makedirs(a.out, exist_ok=True)
    name = os.path.splitext(os.path.basename(src))[0]
    parent = os.path.basename(os.path.dirname(os.path.abspath(src)))
    # 标注文件（NN_annotated）直接用文件名，避免多次渲染互相覆盖
    base = name if a.annotated else (parent if parent else name)
    w, h, nb, nw = render_topdown(lay, os.path.join(a.out, base + "_topdown.png"), cell=a.cell)
    export_2d_json(lay, os.path.join(a.out, base + "_2d.json"))
    print("2D ok: %dx%d px, buildings=%d walls=%d -> %s" % (w, h, nb, nw, a.out))


if __name__ == "__main__":
    main()
