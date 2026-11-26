# -*- coding: utf-8 -*-
"""批量估计已标注建筑的等级（配色匹配，输出 level_est 供人工复核）。

    python tools/infer_levels.py --th th16 --base 03
    python tools/infer_levels.py --all
"""
import argparse
import glob
import json
import os
import sys

import numpy as np
import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from clashlab import level_visual, geo  # noqa: E402

OUT = os.path.join(ROOT, "out", "annotate", "level_estimates.json")


def load_json(p):
    return json.load(open(p, encoding="utf-8"))


def run_one(th, base):
    base_dir = os.path.join(ROOT, "bases", th, base)
    ann_p = os.path.join(ROOT, "out", "annotate", "%s_annotated.json" % base)
    quad_p = os.path.join(ROOT, "out", "annotate", "%s_quad.json" % base)
    img_p = os.path.join(base_dir, "base.png")
    if not (os.path.exists(ann_p) and os.path.exists(img_p)):
        return None
    ann = load_json(ann_p)
    img = cv2.imdecode(np.fromfile(img_p, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return None
    quad = None
    if os.path.exists(quad_p):
        quad = load_json(quad_p).get("quad")
    if quad is None:
        quad = (load_json(os.path.join(base_dir, "layout.json")).get("quad"))
    if quad is None:
        return None
    calib = geo.Calib.from_quad(quad, n=44)
    rows = []
    for b in ann.get("buildings") or []:
        t = str(b.get("type") or "")
        size = 4 if t == "town-hall" else (3 if t not in ("inferno-tower", "hidden-tesla", "air-sweeper",
                                                         "spell-tower", "monolith") else 2)
        if t == "monolith":
            size = 3
        crop = level_visual.crop_building(img, calib, b.get("tile") or [22, 22], size)
        est = level_visual.estimate(crop, t)
        rows.append({"type": t, "tile": list(b.get("tile") or []),
                     "level_est": est["level"], "confidence": est["confidence"],
                     "top": est["top"]})
    return {"th": th, "base": base, "source": ann_p, "quad_source": quad_p if os.path.exists(quad_p) else "layout",
            "buildings": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--th", default="th16")
    ap.add_argument("--base", default=None)
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    targets = []
    if a.all:
        for ann in sorted(glob.glob(os.path.join(ROOT, "out", "annotate", "*_annotated.json"))):
            bid = os.path.basename(ann).split("_")[0]
            targets.append((a.th, bid))
    else:
        targets.append((a.th, a.base))
    results = []
    for th, base in targets:
        r = run_one(th, base)
        if r is None:
            print("skip", base)
            continue
        lv = [x["level_est"] for x in r["buildings"] if x["level_est"]]
        print("[%s] %d 栋，等级估计 %d 条，范围 %s..%s" % (
            base, len(r["buildings"]), len(lv), min(lv) if lv else "-", max(lv) if lv else "-"))
        results.append(r)
    json.dump({"tool": "tools/infer_levels", "results": results}, open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("written:", OUT)


if __name__ == "__main__":
    main()
