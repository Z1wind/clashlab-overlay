# -*- coding: utf-8 -*-
"""构建四角数据集：对社区阵型图跑草地边界检测，自动生成伪标签。

    python tools/build_quad_dataset.py [--max 120]
产物：out/quad_dataset/manifest.json（image/width/height/quad/area_ratio/split）
"""
import argparse, glob, json, os, sys
import numpy as np
import cv2

BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab import calib as calib_mod  # noqa: E402

OUT = os.path.join(BASE, "out", "quad_dataset")
SRC_DIRS = [os.path.join(BASE, "out", "quad_images"), os.path.join(BASE, "out", "sceneries")]


def area_ratio(q, w, h):
    s = 0.0
    for i in range(4):
        s += q[i][0] * q[(i + 1) % 4][1] - q[(i + 1) % 4][0] * q[i][1]
    return abs(s) / 2.0 / float(w * h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=120)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    files = []
    for d in SRC_DIRS:
        files += sorted(glob.glob(os.path.join(d, "*.jpg")) + glob.glob(os.path.join(d, "*.jpeg"))
                        + glob.glob(os.path.join(d, "*.png")))
    files = files[: a.max]
    rows = []
    good = 0
    for f in files:
        img = cv2.imdecode(np.fromfile(f, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            continue
        try:
            calib, meta = calib_mod.detect_village_quad(img, grid_n=44)
        except Exception:
            continue
        quad = meta.get("quad")
        if calib is None or not quad:
            continue
        ratio = area_ratio(quad, img.shape[1], img.shape[0])
        if not (0.15 <= ratio <= 0.95):
            continue
        h = "%08x" % (hash(os.path.basename(f)) & 0xFFFFFFFF)
        split = "val" if int(h, 16) % 5 == 0 else "train"
        rows.append({"image": f, "width": int(img.shape[1]), "height": int(img.shape[0]),
                     "quad": [[round(float(x), 2), round(float(y), 2)] for x, y in quad],
                     "area_ratio": round(ratio, 4), "method": meta.get("method"), "split": split})
        good += 1
    manifest = {"version": 1, "count": len(rows), "ok": good, "total": len(files), "rows": rows,
                "note": "伪标签来自草地边界检测（clashlab.calib.detect_village_quad），仅用于四角模型自监督预训练"}
    json.dump(manifest, open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("[dataset] ok=%d total=%d -> %s" % (good, len(files), os.path.join(OUT, "manifest.json")))
    print("[split] train=%d val=%d" % (sum(1 for r in rows if r["split"] == "train"),
                                       sum(1 for r in rows if r["split"] == "val")))


if __name__ == "__main__":
    main()
