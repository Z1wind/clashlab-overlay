# -*- coding: utf-8 -*-
"""等级对比实测：满级 vs 低等级（敌方建筑 + 我方兵种/英雄）。"""
import json, os, subprocess, sys
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
PY = r"D:\Python313\python.exe"
os.makedirs(os.path.join(BASE, "out", "wargame"), exist_ok=True)
army_path = os.path.join(BASE, "out", "wargame", "army.json")
json.dump({"giant": 10, "wizard": 12}, open(army_path, "w", encoding="utf-8"))

def cli(layout, out, extra=()):
    cmd = [PY, "-u", os.path.join(BASE, "tools", "wargame_cli.py"),
           "--layout", layout, "--army", "@" + army_path,
           "--trials", "20", "--seed", "1", "--quiet", "--out", out] + list(extra)
    p = subprocess.run(cmd, cwd=BASE, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        print("FAIL", p.returncode, p.stderr[-300:])
        return None
    return json.load(open(os.path.join(BASE, out), encoding="utf-8"))

full = cli("bases/th16/03/layout.json", "out/wargame/lv_full.json")
low = cli("out/wargame/layout_lowlevel.json", "out/wargame/lv_low.json")
troop_low = cli("bases/th16/03/layout.json", "out/wargame/lv_troop_low.json",
                ["--troop-levels", "giant=3,wizard=3", "--hero-levels", "queen=10,king=10"])
for name, d in (("满级建筑+满级兵", full), ("低等级建筑", low), ("满级建筑+低等级兵/英雄", troop_low)):
    if d:
        print("%-22s destruction=%s best=%s" % (name, d["destruction"], d["best"]))
