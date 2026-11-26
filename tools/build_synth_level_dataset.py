# -*- coding: utf-8 -*-
"""用 ClashKing 逐级建筑素材合成「类型 + 等级」训练集。

    python tools/build_synth_level_dataset.py --per-sprite 20
产物：E:\ClashLab\datasets\synth_level\{imgs.npy, labels.json}
"""
import argparse, json, os, random
import numpy as np
import cv2

CK = r"E:\ClashLab\assets\clashking"
OUT = r"E:\ClashLab\datasets\synth_level"
SIZE = 96

# ClashKing 目录名 -> 项目类型名
MAP = {
    "air_defense": "air-defense", "air_sweeper": "air-sweeper", "archer_tower": "archer-tower",
    "bomb_tower": "bomb-tower", "cannon": "cannon", "eagle_artillery": "eagle-artillery",
    "firespitter": "firespitter", "hidden_tesla": "hidden-tesla", "inferno_tower": "inferno-tower",
    "monolith": "monolith", "mortar": "mortar", "multi-archer_tower": "multi-archer-tower",
    "multi-gear_tower": "multi-gear-tower", "revenge_tower": "revenge-tower",
    "ricochet_cannon": "ricochet-cannon", "scattershot": "scattershot",
    "spell_tower": "spell-tower", "super_wizard_tower": "super-wizard-tower",
    "x_bow": "x-bow", "town_hall": "town-hall", "clan_castle": "clan-castle",
    "firecracker_tower": "firecracker-tower",
    "gold_mine": "gold-mine", "elixir_collector": "elixir-collector",
    "gold_storage": "gold-storage", "elixir_storage": "elixir-storage",
    "dark_elixir_storage": "dark-elixir-storage", "barracks": "barracks",
    "dark_barracks": "dark-barracks", "army_camp": "army-camp", "laboratory": "laboratory",
    "spell_factory": "spell-factory", "dark_spell_factory": "dark-spell-factory",
}


def load_sprite(path):
    img = cv2.imdecode(np.fromfile(path, np.uint8), cv2.IMREAD_UNCHANGED)
    if img is None:
        return None
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
    if img.shape[2] == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    return img


def background(rng):
    base = rng.choice([[70, 120, 70], [90, 140, 90], [120, 150, 110], [60, 90, 60], [140, 160, 130]])
    small = np.random.RandomState(rng.randint(0, 1 << 30)).randint(0, 60, (6, 6, 3)).astype(np.float32)
    noise = cv2.resize(small, (SIZE, SIZE), interpolation=cv2.INTER_CUBIC)
    bg = np.clip(np.array(base, np.float32)[None, None, :] + noise - 30, 0, 255).astype(np.uint8)
    return bg


def make_sample(sprite, rng):
    h, w = sprite.shape[:2]
    s = rng.uniform(0.45, 1.0) * SIZE / max(h, w)
    nw, nh = max(8, int(w * s)), max(8, int(h * s))
    sp = cv2.resize(sprite, (nw, nh), interpolation=cv2.INTER_AREA)
    ang = rng.uniform(-14, 14)
    M = cv2.getRotationMatrix2D((nw / 2, nh / 2), ang, rng.uniform(0.85, 1.1))
    sp = cv2.warpAffine(sp, M, (nw, nh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT,
                        borderValue=(0, 0, 0, 0))
    bg = background(rng)
    x = rng.randint(-nw // 4, SIZE - 3 * nw // 4)
    y = rng.randint(-nh // 4, SIZE - 3 * nh // 4)
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(SIZE, x + nw), min(SIZE, y + nh)
    if x1 <= x0 or y1 <= y0:
        return bg
    sub = sp[y0 - y:y1 - y, x0 - x:x1 - x]
    if sub.shape[2] == 4:
        a = sub[:, :, 3:4].astype(np.float32) / 255.0
        roi = bg[y0:y1, x0:x1].astype(np.float32)
        bg[y0:y1, x0:x1] = np.clip(roi * (1 - a) + sub[:, :, :3].astype(np.float32) * a, 0, 255).astype(np.uint8)
    # 亮度/对比度/模糊/遮挡
    bg = np.clip(bg.astype(np.float32) * rng.uniform(0.75, 1.25) + rng.uniform(-25, 25), 0, 255).astype(np.uint8)
    if rng.random() < 0.35:
        bg = cv2.GaussianBlur(bg, (3, 3), 0)
    if rng.random() < 0.25:
        cv2.rectangle(bg, (rng.randint(0, SIZE - 8), rng.randint(0, SIZE - 8)),
                      (rng.randint(8, SIZE), rng.randint(8, SIZE)), tuple(rng.randint(0, 120) for _ in range(3)), -1)
    return bg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-sprite", type=int, default=20)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    man = json.load(open(os.path.join(CK, "manifest_buildings.json"), encoding="utf-8"))
    rng = random.Random(a.seed)
    types = sorted(man["buildings"].keys())
    imgs, labels = [], []
    for ck_name in types:
        our = MAP.get(ck_name)
        if not our:
            continue
        levels = man["buildings"][ck_name]
        if len(levels) < 3:
            continue
        max_lv = max(x["level"] for x in levels)
        for item in levels:
            p = os.path.join(CK, item["file"])
            sp = load_sprite(p)
            if sp is None:
                continue
            for _ in range(a.per_sprite):
                imgs.append(make_sample(sp, rng))
                labels.append({"type": our, "level": int(item["level"]), "max_level": int(max_lv)})
    arr = np.stack(imgs)
    os.makedirs(OUT, exist_ok=True)
    np.save(os.path.join(OUT, "imgs.npy"), arr)
    json.dump(labels, open(os.path.join(OUT, "labels.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print("[synth] samples:", len(arr), "types:", len({l["type"] for l in labels}),
          "levels:", len({(l["type"], l["level"]) for l in labels}), "->", OUT)


if __name__ == "__main__":
    main()
