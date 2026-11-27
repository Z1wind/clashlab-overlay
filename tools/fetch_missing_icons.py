# -*- coding: utf-8 -*-
import json, os, sys, urllib.request, urllib.parse
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "assets", "units_real")
TOKEN = os.environ.get("GH_TOKEN") or ""
API = "https://api.github.com"
def gh(u):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore")) if False else json.loads(r.read().decode())
# 查找 ClashKingAssets 里 root rider / revive spell
for sub, kw, uid in (("troops", "root", "root-rider"), ("spells", "revive", "revive")):
    try:
        items = gh(API + "/repos/ClashKingInc/ClashKingAssets/contents/assets/" + sub)
    except Exception as e:
        print(sub, "list fail", str(e)[:80]); continue
    names = [it["name"] for it in items]
    cand = [n for n in names if kw in n.lower()]
    print(sub, "matches:", cand[:6])
    for n in cand:
        # 文件或目录：目录内取 level_1.webp 或第一个图片
        try:
            if n.lower().endswith((".webp", ".png", ".jpg")):
                url = "https://raw.githubusercontent.com/ClashKingInc/ClashKingAssets/master/assets/%s/%s" % (sub, urllib.parse.quote(n))
                data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "c"}), timeout=60).read()
                dst = os.path.join(OUT, uid + os.path.splitext(n)[1])
                open(dst, "wb").write(data)
                print("saved", dst, len(data)); break
            else:
                inner = gh(API + "/repos/ClashKingInc/ClashKingAssets/contents/assets/%s/%s" % (sub, n))
                imgs = [x for x in inner if x["name"].lower().endswith((".webp", ".png"))]
                if not imgs:
                    continue
                pick = imgs[0]
                data = urllib.request.urlopen(urllib.request.Request(pick["download_url"], headers={"User-Agent": "c"}), timeout=60).read()
                dst = os.path.join(OUT, uid + os.path.splitext(pick["name"])[1])
                open(dst, "wb").write(data)
                print("saved", dst, len(data), "from", pick["name"]); break
        except Exception as e:
            print("dl fail", n, str(e)[:80])
