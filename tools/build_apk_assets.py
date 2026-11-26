# -*- coding: utf-8 -*-
"""生成 APK 内 assets：6 张阵图 + data.js（quad + 已标注建筑）。"""
import glob, json, os, shutil, sys

BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab import assets

A = os.path.join(BASE, "out", "annotate")
DEST = r"E:\ClashLab\android\assets"
IMG = os.path.join(DEST, "img")
os.makedirs(IMG, exist_ok=True)

CN = {}
for name, st in assets.STATS.items():
    CN[name] = st.get("cn") or name
CN.update({
    "gold-mine": "金矿", "elixir-collector": "圣水收集器", "dark-elixir-drill": "暗黑重油钻井",
    "gold-storage": "金币仓库", "elixir-storage": "圣水仓库", "dark-elixir-storage": "暗黑重油仓库",
    "barracks": "兵营", "dark-barracks": "暗黑兵营", "army-camp": "训练营", "laboratory": "实验室",
    "spell-factory": "法术工厂", "dark-spell-factory": "暗黑法术工厂", "builder-hut": "建筑工人小屋",
    "builders-hut": "建筑工人小屋", "clan-castle": "部落城堡", "bomb": "炸弹", "spring-trap": "弹簧陷阱",
    "air-bomb": "空中炸弹", "giant-bomb": "巨型炸弹", "seeking-air-mine": "搜空地雷",
    "tornado-trap": "龙卷风陷阱", "skeleton-trap": "骷髅陷阱", "giga-bomb": "巨型特斯拉炸弹",
    "workshop": "工坊", "pet-house": "宠物屋", "blacksmith": "铁匠铺", "hero-hall": "英雄大厅",
})

def load(p, default=None):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return default

bases = []
for i in range(1, 7):
    bid = "%02d" % i
    ann = load(os.path.join(A, bid + "_annotated.json"))
    if not ann:
        print("skip", bid); continue
    base_png = os.path.join(BASE, "bases", "th16", bid, "base.png")
    if not os.path.exists(base_png):
        print("no image", bid); continue
    dst_img = os.path.join(IMG, bid + ".png")
    if not os.path.exists(dst_img) or os.path.getsize(dst_img) != os.path.getsize(base_png):
        shutil.copyfile(base_png, dst_img)
    quad = None
    q = load(os.path.join(A, bid + "_quad.json"))
    if isinstance(q, dict):
        quad = q.get("quad")
    if not quad:
        lay = load(os.path.join(BASE, "bases", "th16", bid, "layout.json"), {}) or {}
        quad = lay.get("quad")
    buildings = []
    for b in ann.get("buildings") or []:
        buildings.append({"type": b.get("type"), "tile": b.get("tile"), "level": b.get("level")})
    bases.append({"id": bid, "name": ann.get("name") or bid, "img": "img/" + bid + ".png",
                  "quad": quad, "buildings": buildings, "walls": ann.get("walls") or [],
                  "grid": int(ann.get("grid") or 44)})
    print(bid, "buildings:", len(buildings), "quad:", "yes" if quad else "NO")

data = {"version": 1, "cn": CN, "bases": bases}
out = os.path.join(DEST, "data.js")
with open(out, "w", encoding="utf-8") as f:
    f.write("window.CLASH_DATA = ")
    json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    f.write(";\n")
print("data.js", os.path.getsize(out), "bytes; images:", len(glob.glob(os.path.join(IMG, "*.png"))))
