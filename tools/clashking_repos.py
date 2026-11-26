# -*- coding: utf-8 -*-
import json, os, urllib.request
TOKEN = os.environ["GH_TOKEN"]
def api(u):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "clashlab", "Accept": "application/vnd.github+json"}
    with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))

user = "ClashKingInc"
prof = api("https://api.github.com/users/" + user)
print("user:", prof.get("login"), "| name:", prof.get("name"), "| repos:", prof.get("public_repos"),
      "| bio:", (prof.get("bio") or "")[:120])
repos = []
page = 1
while page <= 3:
    chunk = api("https://api.github.com/users/%s/repos?per_page=100&page=%d&type=all&sort=updated" % (user, page))
    if not chunk: break
    repos += chunk
    if len(chunk) < 100: break
    page += 1
print("total repos:", len(repos))
lines = []
for r in sorted(repos, key=lambda x: -(x.get("stargazers_count") or 0)):
    lic = (r.get("license") or {}).get("spdx_id") if r.get("license") else None
    lines.append({
        "name": r["name"], "desc": (r.get("description") or "")[:110], "lang": r.get("language"),
        "stars": r.get("stargazers_count"), "size_kb": r.get("size"), "license": lic,
        "topics": r.get("topics") or [], "updated": (r.get("updated_at") or "")[:10],
        "archived": r.get("archived"),
    })
json.dump(lines, open(os.path.join(r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat", "out", "clashking_repos.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for x in lines:
    print("%-34s %5sstar %6sKB %-12s %-10s %s" % (x["name"], x["stars"], x["size_kb"], x["lang"], x["license"], x["desc"]))
