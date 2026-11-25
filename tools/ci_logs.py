# -*- coding: utf-8 -*-
import io, json, os, urllib.request, zipfile
TOKEN = os.environ["GH_TOKEN"]
REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"
run_id = 45599992802
req = urllib.request.Request(REPO + "/actions/runs/%d/logs" % run_id,
                             headers={"Authorization": "token " + TOKEN, "User-Agent": "c"})
with urllib.request.urlopen(req, timeout=120) as r:
    data = r.read()
print("logs bytes:", len(data))
z = zipfile.ZipFile(io.BytesIO(data))
for name in z.namelist():
    if "test" in name.lower() or "Unit" in name:
        txt = z.read(name).decode("utf-8", "replace")
        tail = txt.splitlines()[-60:]
        print("=== ", name)
        for l in tail:
            print(l.encode("ascii", "replace").decode()[:160])
        break
