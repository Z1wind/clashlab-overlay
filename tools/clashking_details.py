# -*- coding: utf-8 -*-
import base64, json, os, urllib.request
TOKEN = os.environ["GH_TOKEN"]
def api(u):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "clashlab", "Accept": "application/vnd.github+json"}
    with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))
U = "ClashKingInc"
repos = json.load(open(r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\clashking_repos.json", encoding="utf-8"))
out = []
for r in repos:
    name = r["name"]
    if name.startswith(".") or name == "num2words":
        continue
    info = {"name": name, "readme": "", "dirs": [], "files": [], "branch": None}
    try:
        repo = api("https://api.github.com/repos/%s/%s" % (U, name))
        br = repo.get("default_branch") or "main"
        info["branch"] = br
        try:
            rd = api("https://api.github.com/repos/%s/%s/readme" % (U, name))
            txt = base64.b64decode(rd.get("content") or "").decode("utf-8", "ignore")
            info["readme"] = txt[:900]
        except Exception as e:
            info["readme"] = "(no readme: %s)" % str(e)[:40]
        try:
            tr = api("https://api.github.com/repos/%s/%s/git/trees/%s" % (U, name, br))
            for t in (tr.get("tree") or [])[:30]:
                (info["dirs"] if t["type"] == "tree" else info["files"]).append(t["path"])
        except Exception as e:
            info["dirs"].append("(tree err: %s)" % str(e)[:30])
    except Exception as e:
        info["readme"] = "ERR " + str(e)[:80]
    out.append(info)
json.dump(out, open(r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\clashking_repo_details.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for x in out:
    print("=" * 100)
    print("REPO:", x["name"], "| branch:", x["branch"])
    print("  dirs:", ", ".join(x["dirs"][:14]) or "-")
    print("  files:", ", ".join(x["files"][:14]) or "-")
    print("  README:", " ".join(x["readme"].split())[:400])
