# -*- coding: utf-8 -*-
import json, os, urllib.request
TOKEN = os.environ["GH_TOKEN"]
def get(u):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))
for user in ("akermu666", "drkostas"):
    try:
        info = get("https://api.github.com/users/" + user)
        print("=" * 20, user, "| public_repos:", info.get("public_repos"), "| bio:", (info.get("bio") or "")[:120])
        repos = get("https://api.github.com/users/%s/repos?per_page=100&sort=updated" % user)
        for r in repos[:25]:
            print("  %-40s stars=%-5s lang=%-10s | %s" % (r["name"], r.get("stargazers_count"), r.get("language"),
                                                          (r.get("description") or "")[:80]))
    except Exception as e:
        print(user, "ERR", str(e)[:100])
