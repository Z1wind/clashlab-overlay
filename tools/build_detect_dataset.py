# -*- coding: utf-8 -*-
"""合成检测数据集：ClashKing 立绘 → 草地背景上随机排布，YOLO 格式。
排除 firespitter（用户误标，训练忽略）。"""
import glob, os, random, shutil, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
SPR = os.path.join(BASE, "assets", "clashking", "buildings")
OUT = os.path.join(BASE, "datasets", "detect")
EXCLUDE = {"firespitter", "wall"}
SIZE = 640
random.seed(7)
np.random.seed(7)

def load_sprites():
    types = sorted(d for d in os.listdir(SPR) if os.path.isdir(os.path.join(SPR, d)) and d not in EXCLUDE)
    bank = {}
    for t in types:
        files = glob.glob(os.path.join(SPR, t, "level_*.webp"))
        def lv(p):
            n = os.path.basename(p)[6:-5]
            return int(n) if n.isdigit() else 0
        files = sorted(files, key=lv)[-4:]
        imgs = []
        for f in files:
            im = cv2.imdecode(np.fromfile(f, np.uint8), cv2.IMREAD_UNCHANGED)
            if im is not None and im.shape[2] == 4 and (im[:, :, 3] > 30).sum() > 200:
                imgs.append(im)
        if imgs:
            bank[t] = imgs
    return types, bank

def grass_bg():
    h, w = SIZE, SIZE
    base = np.zeros((h, w, 3), np.uint8)
    base[:, :] = (60, 120, 55)
    noise = np.random.randint(0, 42, (h, w, 1), np.int16)
    base = np.clip(base.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    for _ in range(np.random.randint(1, 4)):
        c = tuple(int(v) for v in np.random.randint(0, 255, 3))
        r = np.random.randint(30, 140)
        mask = np.zeros((h, w), np.uint8)
        cv2.ellipse(mask, (np.random.randint(0, w), np.random.randint(0, h)), (r, r // 2),
                    np.random.randint(0, 180), 0, 360, 255, -1)
        mask = cv2.GaussianBlur(mask, (31, 31), 0)
        base = (base * (1 - mask[..., None] / 255.0) + np.array(c, np.uint8) * (mask[..., None] / 255.0)).astype(np.uint8)
    return cv2.GaussianBlur(base, (3, 3), 0)

def paste(im, bg, x, y, sc):
    h = max(16, int(im.shape[0] * sc)); w = max(16, int(im.shape[1] * sc))
    spr = cv2.resize(im, (w, h), interpolation=cv2.INTER_AREA)
    x = max(0, min(SIZE - w, x)); y = max(0, min(SIZE - h, y))
    a = spr[:, :, 3:4].astype(np.float32) / 255.0
    roi = bg[y:y + h, x:x + w].astype(np.float32)
    bg[y:y + h, x:x + w] = (roi * (1 - a) + spr[:, :, :3].astype(np.float32) * a).astype(np.uint8)
    return x, y, w, h

def make(idx, split, types, bank, n_sprites):
    bg = grass_bg()
    labels = []
    used = []
    for _ in range(n_sprites):
        t = random.choice(types)
        spr = random.choice(bank[t])
        sc = random.uniform(0.07, 0.20) * (640.0 / max(spr.shape[1], 80))
        for _try in range(6):
            x = random.randint(-10, SIZE - 20); y = random.randint(-10, SIZE - 20)
            if all(abs(x - ux) > 40 or abs(y - uy) > 40 for ux, uy in used):
                break
        x, y, w, h = paste(spr, bg, x, y, sc)
        if w < 12 or h < 12:
            continue
        used.append((x + w // 2, y + h // 2))
        labels.append("%d %.6f %.6f %.6f %.6f" % (types.index(t),
                      (x + w / 2) / SIZE, (y + h / 2) / SIZE, w / SIZE, h / SIZE))
    img_dir = os.path.join(OUT, "images", split); lab_dir = os.path.join(OUT, "labels", split)
    cv2.imencode(".jpg", bg, [cv2.IMWRITE_JPEG_QUALITY, 92])[1].tofile(os.path.join(img_dir, "%06d.jpg" % idx))
    with open(os.path.join(lab_dir, "%06d.txt" % idx), "w", encoding="utf-8") as f:
        f.write("\n".join(labels))

def main():
    types, bank = load_sprites()
    print("types:", len(types), "excluded:", sorted(EXCLUDE))
    for split, n in (("train", 1500), ("val", 240)):
        img_dir = os.path.join(OUT, "images", split); lab_dir = os.path.join(OUT, "labels", split)
        shutil.rmtree(img_dir, ignore_errors=True); shutil.rmtree(lab_dir, ignore_errors=True)
        os.makedirs(img_dir, exist_ok=True); os.makedirs(lab_dir, exist_ok=True)
        for i in range(n):
            make(i, split, types, bank, random.randint(8, 16))
        print(split, n, "done", flush=True)
    with open(os.path.join(OUT, "data.yaml"), "w", encoding="utf-8") as f:
        f.write("path: %s\n" % OUT.replace("\\", "/"))
        f.write("train: images/train\nval: images/val\n")
        f.write("names:\n")
        for i, t in enumerate(types):
            f.write("  %d: %s\n" % (i, t))
    print("data.yaml written; classes:", len(types))

if __name__ == "__main__":
    main()
