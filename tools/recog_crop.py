# -*- coding: utf-8 -*-
# recog_crop.py — 候选建筑放大裁片（纯离线只读）；manifest: {name:[block,x,y,w,h]}
import os, json, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BLK = os.path.join(ROOT, "out", "overlay", "blocks")
OUT = os.path.join(ROOT, "tools", "base_out")
os.makedirs(OUT, exist_ok=True)
manifest = {
    "c_mortar_b09":      ["b09", 160, 30, 300, 250],
    "c_wiztower_b09":    ["b09", 440, 120, 320, 320],
    "c_chainpot_b09":    ["b09", 240, 340, 260, 210],
    "c_dome_b10":        ["b10", 0, 0, 280, 300],
    "c_conetower_b10":   ["b10", 580, 0, 340, 280],
    "c_xbow_b11":        ["b11", 560, 120, 320, 220],
    "c_conetower_b11":   ["b11", 100, 0, 320, 260],
    "c_purplecrystal_b12": ["b12", 560, 170, 240, 240],
    "c_coiltower_b12":   ["b12", 760, 190, 190, 300],
    "c_bluegun_b12":     ["b12", 360, 370, 360, 190],
    "c_purplegold_b13":  ["b13", 0, 110, 210, 440],
    "c_redcannon_b13":   ["b13", 740, 0, 210, 200],
    "c_redgold_b04":     ["b04", 380, 250, 330, 290],
    "c_whitetower_b05":  ["b05", 350, 120, 260, 320],
    "c_bluegun_b14":     ["b14", 410, 290, 330, 240],
}
for name, (b, x, y, w, h) in manifest.items():
    im = cv2.imdecode(np.fromfile(os.path.join(BLK, b + ".png"), dtype=np.uint8), cv2.IMREAD_COLOR)
    crop = im[y:y + h, x:x + w]
    big = cv2.resize(crop, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
    cv2.imencode(".png", big)[1].tofile(os.path.join(OUT, name + ".png"))
print("saved", len(manifest))
