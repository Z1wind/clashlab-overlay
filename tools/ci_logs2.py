# -*- coding: utf-8 -*-
import io, json, os, urllib.request, zipfile
TOKEN = os.environ["GH_TOKEN"]
REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"

def call(url, accept="application/vnd.github+json"):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": accept}
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))

runs = call(REPO + "/actions/runs?per_page=1")
run_id = runs["workflow_runs"][0]["id"]
print("run id:", run_id)
req = urllib.request.Request(REPO + "/actions/runs/%d/logs" % run_id,
                             headers={"Authorization": "token " + TOKEN, "User-Agent": "c"})
with urllib.request.urlopen(req, timeout=120) as r:
    data = r.read()
z = zipfile.ZipFile(io.BytesIO(data))
name = [n for n in z.namelist() if n.endswith("test.txt") or "test" in n][0]
txt = z.read(name).decode("utf-8", "replace")
lines = txt.splitlines()
# 只抓错误/失败行
for l in lines:
    u = l.encode("ascii", "replace").decode()
    if ("ERROR:" in u or "FAIL:" in u or "Error" in u or "FAILED" in u or "Ran " in u or "UnicodeEncode" in u):
        print(u[:200])
