# -*- coding: utf-8 -*-
"""标注质检：对齐/覆盖/重复/范围，给 PASS/WARN/FAIL 结论。

用法: python tools/label_qa.py --labels "a.json;b.json"
"""
import argparse, json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import cv2, numpy as np
from clashlab.geo import Calib
EXPECTED = {"town-hall","eagle-artillery","monolith","scattershot","x-bow","inferno-tower","clan-castle",
            "air-defense","air-sweeper","wizard-tower","archer-tower","cannon","mortar","bomb-tower",
            "hidden-tesla","builder-hut","army-camp","barracks","dark-barracks","spell-factory",
            "dark-spell-factory","gold-mine","elixir-collector","dark-elixir-drill","gold-storage",
            "elixir-storage","dark-elixir-storage","laboratory","workshop","pet-house","hero-hall",
            "blacksmith","spell-tower","ricochet-cannon","multi-archer-tower","firespitter"}
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", required=True)
    ap.add_argument("--img-root", default=os.path.join(BASE, "android", "assets"))
    a = ap.parse_args()
    files = [x.strip() for x in a.labels.replace("\n", ";").split(";") if x.strip()]
    fails = warns = 0
    for path in files:
        try:
            d = json.load(open(path, encoding="utf-8"))
        except Exception as e:
            print("FAIL", path, "JSON 解析失败", e); fails += 1; continue
        name = os.path.basename(path)
        problems = []; notes = []
        if d.get("version") != 2: problems.append("version!=2")
        cn = d.get("corners_norm") or []
        if len(cn) != 4: problems.append("corners_norm=%d" % len(cn))
        img_rel = d.get("image") or ""
        img_path = os.path.join(a.img_root, img_rel)
        img = cv2.imdecode(np.fromfile(img_path, np.uint8), cv2.IMREAD_COLOR) if os.path.exists(img_path) else None
        if img is None: problems.append("图片不存在:" + img_rel)
        b = d.get("buildings") or []
        if not (50 <= len(b) <= 110): problems.append("建筑数异常:%d" % len(b))
        tiles = [tuple(x.get("tile") or []) for x in b]
        bad = [t for t in tiles if len(t) != 2 or not (0 <= t[0] <= 43 and 0 <= t[1] <= 43)]
        if bad: problems.append("越界/非法 tile:%d" % len(bad))
        dup = len(tiles) - len(set(tiles))
        if dup > 0: problems.append("重复 tile:%d" % dup)
        types = {x.get("type") for x in b}
        missing = sorted(EXPECTED - types)
        if len(missing) > 6: notes.append("缺类型:" + ",".join(missing[:8]))
        align = None
        if img is not None and len(cn) == 4 and len(b) > 0:
            wn, hn = d.get("image_size") or [img.shape[1], img.shape[0]]
            quad = np.float32([[u*wn, v*hn] for u, v in cn])
            cal = Calib.from_quad(quad, n=44)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY); lap = cv2.Laplacian(gray, cv2.CV_32F)
            energy = cv2.blur(lap*lap, (9,9))
            vals = []
            for x, y in tiles:
                px, py = cal.tile_to_px(x + .5, y + .5)
                xi, yi = int(px), int(py)
                if 0 <= xi < img.shape[1] and 0 <= yi < img.shape[0]: vals.append(energy[yi, xi])
            rng = np.random.default_rng(0)
            rv = []
            for _ in range(300):
                xi = int(rng.integers(0, img.shape[1])); yi = int(rng.integers(0, img.shape[0]))
                rv.append(energy[yi, xi])
            align = float(np.mean(vals) / max(1e-6, np.mean(rv))) if vals else None
            if align is not None:
                if align < 1.2: problems.append("对齐可疑 ratio=%.2f" % align)
                elif align < 1.6: notes.append("对齐偏弱 ratio=%.2f" % align)
        verdict = "FAIL" if problems else ("WARN" if notes else "PASS")
        if verdict == "FAIL": fails += 1
        elif verdict == "WARN": warns += 1
        print("%-4s %-24s bld=%-3d types=%-2d align=%s %s" % (verdict, name, len(b), len(types),
              ("%.2f" % align) if align else "-", ("; ".join(problems) if problems else ("; ".join(notes) if notes else ""))))
    total = len(files)
    print("\nSUMMARY: %d files, PASS=%d WARN=%d FAIL=%d" % (total, total-warns-fails, warns, fails))
    return 0 if fails == 0 else 1
if __name__ == "__main__":
    raise SystemExit(main())
