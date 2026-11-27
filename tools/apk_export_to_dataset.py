# -*- coding: utf-8 -*-
"""把 APK 导出的标注（v2：image_size + corners_norm + buildings）转成训练数据集。

python tools/apk_export_to_dataset.py --export out/apk_qa/v21_export.json --out datasets/apk_real
"""
import argparse, json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
S = 96


def load_export(path):
    doc = json.load(open(path, encoding="utf-8"))
    if "bases" in doc:
        return doc["bases"]
    return [doc]


def crops_for_base(base, img_root):
    from clashlab.geo import Calib
    rel = base["image"]
    if rel.startswith("img/"):
        rel = rel
    img_path = os.path.join(img_root, rel)
    img = cv2.imdecode(np.fromfile(img_path, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(img_path)
    if "corners_norm" in base:
        wn, hn = base["image_size"]
        quad = np.float32([[u * wn, v * hn] for u, v in base["corners_norm"]])
    else:
        quad = np.float32(base["corners"])
    cal = Calib.from_quad(quad, n=44)
    out = []
    for b in base.get("buildings") or []:
        t = b.get("type")
        if not t or t == "__bg__":
            continue
        x, y = int(b["tile"][0]), int(b["tile"][1])
        side = 4
        x0 = max(0, x - 1); y0 = max(0, y - 1)
        x1 = min(44, x0 + side); y1 = min(44, y0 + side)
        x0 = max(0, x1 - side); y0 = max(0, y1 - side)
        p = [cal.tile_to_px(x0, y0), cal.tile_to_px(x1, y0), cal.tile_to_px(x1, y1), cal.tile_to_px(x0, y1)]
        H = cv2.getPerspectiveTransform(np.float32(p), np.float32([[0, 0], [S, 0], [S, S], [0, S]]))
        crop = cv2.warpPerspective(img, H, (S, S), flags=cv2.INTER_AREA)
        out.append((crop, {"type": t, "name": b.get("name") or t, "tile": [x, y]}))
    return out, img_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", required=True)
    ap.add_argument("--img-root", default=os.path.join(BASE, "android", "assets"))
    ap.add_argument("--out", default=os.path.join(BASE, "datasets", "apk_real"))
    a = ap.parse_args()
    bases = load_export(a.export)
    imgs, labels = [], []
    for base in bases:
        crops, img_path = crops_for_base(base, a.img_root)
        for c, lab in crops:
            imgs.append(c); labels.append(lab)
        print("base", os.path.basename(img_path), "crops:", len(crops))
    os.makedirs(a.out, exist_ok=True)
    if not imgs:
        print("no crops"); return 2
    np.save(os.path.join(a.out, "imgs.npy"), np.stack(imgs, 0))
    json.dump(labels, open(os.path.join(a.out, "labels.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("saved", len(labels), "crops ->", a.out, "| types:", len({l["type"] for l in labels}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
