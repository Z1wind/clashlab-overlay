# -*- coding: utf-8 -*-
import json, os, sys, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
spec = json.load(open(os.path.join(BASE, "out", "api", "clashking_openapi.json"), encoding="utf-8"))
paths = spec.get("paths") or {}
print("== 公开端点里带 player/clan 的（前 40） ==")
n = 0
for p, item in paths.items():
    for m, op in item.items():
        if m not in ("get", "post"): continue
        sec = op.get("security", item.get("security"))
        is_pub = (sec == []) or (sec is None)
        if is_pub and ("/player" in p or "/clan" in p):
            n += 1
            if n <= 40:
                print("%-58s %-4s %s" % (p[:58], m.upper(), (op.get("summary") or "")[:52]))
print("public player/clan endpoints:", n)
CK = "https://api.clashk.ing"
def get(u):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "clashlab"}), timeout=30) as r:
            return r.status, r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read(300).decode("utf-8", "ignore")
    except Exception as e:
        return "ERR", str(e)[:120]
for tag in ("%23PLVYQ0G2U", "PLVYQ0G2U", "%23PUP9P88R"):
    for q in ("", "?limit=2", "?limit=5&page=1"):
        st, body = get(CK + "/v2/clan/%s/wars%s" % (tag, q))
        try:
            j = json.loads(body); cnt = len(j.get("items") or []); extra = "ok"
        except Exception:
            cnt = "?"; extra = body[:90].replace("\n", " ")
        print("wars", tag, q or "(none)", "->", st, "items:", cnt, extra if cnt == "?" else "")
