# -*- coding: utf-8 -*-
"""生成战报 HTML：python tools/make_battle_report.py --layout out/annotate/06_annotated.json --th 16"""
import argparse, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
from clashlab import battle_report

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layout", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--th", type=int, default=None)
    ap.add_argument("--open", action="store_true")
    a = ap.parse_args()
    r = battle_report.build(a.layout, out_path=a.out, th=a.th, open_after=a.open)
    print("report:", r["path"], r["bytes"], "bytes | grade", r["grade"], r["score"], "| stars", r.get("stars"))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
