# -*- coding: utf-8 -*-
"""下载真实兵种/法术/英雄图标（Statscell/clash-assets, MIT）到 assets/units_real/。"""
import json, os, re, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ.get("GH_TOKEN") or ""
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "assets", "units_real")
os.makedirs(OUT, exist_ok=True)
API = "https://api.github.com"
REPO = "Statscell/clash-assets"
def gh(u):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "clashlab", "Accept": "application/vnd.github+json"}
    with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))
items = gh(API + "/repos/%s/contents/troops/icons" % REPO)
files = [it["name"] for it in items if it["type"] == "file"]
print("remote icons:", len(files))
def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())
index = {}
for f in files:
    index.setdefault(norm(os.path.splitext(f)[0]), f)
WANT = {
 "miner": "Miner", "hog-rider": "Hog Rider", "healer": "Healer", "balloon": "Balloon",
 "edrag": "Electro Dragon", "dragon": "Dragon", "dragon-rider": "Dragon Rider",
 "root-rider": "Root Rider", "yeti": "Yeti", "witch": "Witch", "super-witch": "Super Witch",
 "bowler": "Bowler", "pekka": "PEKKA", "golem": "Golem", "ice-golem": "Ice Golem",
 "valkyrie": "Valkyrie", "wizard": "Wizard", "baby-dragon": "Baby Dragon",
 "barbarian": "Barbarian", "archer": "Archer", "wall-breaker": "Wall Breaker",
 "rage": "Rage Spell", "freeze": "Freeze Spell", "heal": "Healing Spell", "jump": "Jump Spell",
 "haste": "Haste Spell", "clone": "Clone Spell", "poison": "Poison Spell",
 "earthquake": "Earthquake Spell", "invisibility": "Invisibility Spell",
 "skeleton": "Skeleton Spell", "bat": "Bat Spell", "recall": "Recall Spell", "revive": "Revive Spell",
 "queen": "Archer Queen", "king": "Barbarian King", "warden": "Grand Warden",
 "royal-champion": "Royal Champion", "minion-prince": "Minion Prince",
}
ALIASES = {"pekka": ["pekka", "PEKKA", "P.E.K.K.A", "Pekka"], "edrag": ["Electro Dragon", "ElectroDragon"],
           "heal": ["Healing Spell", "Heal Spell"], "revive": ["Revive Spell"]}
done, missing = [], []
for uid, name in WANT.items():
    cands = [name] + ALIASES.get(uid, [])
    match = None
    for c in cands:
        if norm(c) in index:
            match = index[norm(c)]; break
    if not match:
        for key, f in index.items():
            if norm(name) in key or key in norm(name):
                match = f; break
    if not match:
        missing.append((uid, name)); continue
    url = "https://raw.githubusercontent.com/%s/master/troops/icons/%s" % (REPO, urllib.parse.quote(match))
    dst = os.path.join(OUT, uid + os.path.splitext(match)[1])
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "clashlab"}), timeout=60) as r:
            data = r.read()
        open(dst, "wb").write(data)
        done.append((uid, match, len(data)))
    except Exception as e:
        missing.append((uid, name + " dl:" + str(e)[:40]))
print("downloaded:", len(done), "| missing:", len(missing))
for m in missing:
    print(" MISS", m)
for d in done[:8]:
    print(" OK", d)
