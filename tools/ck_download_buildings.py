# -*- coding: utf-8 -*-
"""下载 ClashKingAssets 建筑逐级素材（CDN，存 E 盘）。"""
import json, os, re, urllib.request
TOKEN = os.environ["GH_TOKEN"]
DEST = r"E:\ClashLab\assets\clashking"
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
def api(u):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "clashlab", "Accept": "application/vnd.github+json"}
    with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))
def fetch(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 500:
        return os.path.getsize(path)
    req = urllib.request.Request(url, headers={"User-Agent": "clashlab"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "wb").write(data)
    return len(data)

U, R = "ClashKingInc", "ClashKingAssets"
bdirs = api("https://api.github.com/repos/%s/%s/contents/assets/buildings/home-village" % (U, R))
manifest = {"buildings": {}, "downloaded": 0}
for b in bdirs:
    if b["type"] != "dir":
        continue
    name = b["name"]
    try:
        files = api("https://api.github.com/repos/%s/%s/contents/assets/buildings/home-village/%s" % (U, R, name))
    except Exception as e:
        print("list fail", name, str(e)[:50]); continue
    levels = []
    for f in files:
        m = re.match(r"level_(\d+)\.(webp|png)$", f["name"])
        if not m:
            continue
        lv = int(m.group(1))
        url = "https://assets.clashk.ing/buildings/home-village/%s/%s" % (name, f["name"])
        dst = os.path.join(DEST, "buildings", name, "level_%d.%s" % (lv, m.group(2)))
        try:
            size = fetch(url, dst)
            levels.append({"level": lv, "file": "buildings/%s/level_%d.%s" % (name, lv, m.group(2)), "bytes": size})
            manifest["downloaded"] += 1
        except Exception as e:
            print("dl fail", name, lv, str(e)[:50])
    levels.sort(key=lambda x: x["level"])
    manifest["buildings"][name] = levels
    print("%-24s levels=%d" % (name, len(levels)), flush=True)
json.dump(manifest, open(os.path.join(DEST, "manifest_buildings.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("DONE files:", manifest["downloaded"], "types:", len(manifest["buildings"]))
