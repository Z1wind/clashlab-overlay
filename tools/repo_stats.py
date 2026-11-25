# -*- coding: utf-8 -*-
"""查询仓库星标/关注/复刻/浏览等公开指标与名单。"""
import json, os, urllib.request, urllib.error
TOKEN = os.environ["GH_TOKEN"]; REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"
def get(url):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=60) as r:
            return json.loads(r.read().decode("utf-8", "ignore"))
    except urllib.error.HTTPError as e:
        return {"_err": e.code, "_body": e.read().decode("utf-8", "ignore")[:160]}
repo = get(REPO)
print("counts: stars=%s watchers=%s forks=%s subscribers=%s" % (
    repo.get("stargazers_count"), repo.get("watchers_count"), repo.get("forks_count"), repo.get("subscribers_count") if "subscribers_count" in repo else "?"))
stars = get(REPO + "/stargazers?per_page=100")
if isinstance(stars, list):
    print("stargazers list:", len(stars))
    for s in stars[:20]:
        print("  ", s.get("login"), "|", (s.get("starred_at") or ""))
else:
    print("stargazers:", stars)
watchers = get(REPO + "/subscribers?per_page=100")
if isinstance(watchers, list):
    print("watchers(订阅) list:", len(watchers))
    for w in watchers[:20]:
        print("  ", w.get("login"))
else:
    print("watchers:", watchers)
forks = get(REPO + "/forks?per_page=100")
print("forks list:", len(forks) if isinstance(forks, list) else forks)
issues = get(REPO + "/issues?state=all&per_page=100")
print("issues:", len(issues) if isinstance(issues, list) else issues)
views = get(REPO + "/traffic/views")
print("traffic views:", views if "_err" in views else {"count": views.get("count"), "uniques": views.get("uniques")})
clones = get(REPO + "/traffic/clones")
print("traffic clones:", clones if "_err" in clones else {"count": clones.get("count"), "uniques": clones.get("uniques")})
