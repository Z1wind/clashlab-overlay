# -*- coding: utf-8 -*-
"""解析 ClashKing OpenAPI：统计端点 + 区分公开/需 token + 列出与我们相关的公开端点。"""
import json, os, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "out", "api")
os.makedirs(OUT, exist_ok=True)
path = os.path.join(OUT, "clashking_openapi.json")
if not os.path.exists(path) or os.path.getsize(path) < 1_000_000:
    with urllib.request.urlopen(urllib.request.Request("https://api.clashk.ing/openapi.json",
            headers={"User-Agent": "clashlab"}), timeout=120) as r:
        open(path, "wb").write(r.read())
spec = json.load(open(path, encoding="utf-8"))
paths = spec.get("paths") or {}
print("openapi:", spec.get("openapi"), "| paths:", len(paths))
sec_names = list((spec.get("components", {}).get("securitySchemes") or {}).keys())
print("security schemes:", sec_names)
public, protected = [], []
for p, item in paths.items():
    for m, op in item.items():
        if m not in ("get", "post", "put", "delete"):
            continue
        sec = op.get("security")
        if sec is None:
            sec = item.get("security")
        is_public = (sec == []) or (sec is None)
        (public if is_public else protected).append((p, m, (op.get("summary") or "")[:60]))
print("public:", len(public), "| protected:", len(protected))
KEY = ("player", "clan", "war", "raid", "legend", "season", "static", "leaderboard", "base", "troop")
print("\n== 公开端点（keywords） ==")
for p, m, s in public:
    if any(k in p.lower() or k in s.lower() for k in KEY):
        print("%-52s %-4s %s" % (p[:52], m.upper(), s))
print("\n== 需 token 端点（前 20） ==")
for p, m, s in protected[:20]:
    print("%-52s %-4s %s" % (p[:52], m.upper(), s))
