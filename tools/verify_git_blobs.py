# -*- coding: utf-8 -*-
import json, os, subprocess, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ["GH_TOKEN"]; REPO = "Z1wind/clashlab-overlay"
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
g = r"E:\Temp\mingit2\cmd\git.exe"
h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
head = json.loads(urllib.request.urlopen(urllib.request.Request("https://api.github.com/repos/%s/commits/main" % REPO, headers=h), timeout=60).read().decode())
print("REMOTE_COMMIT", head["sha"][:12], head["commit"]["author"]["date"], "|", head["commit"]["message"].splitlines()[0][:60])
tree = json.loads(urllib.request.urlopen(urllib.request.Request("https://api.github.com/repos/%s/git/commits/%s" % (REPO, head["sha"]), headers=h), timeout=60).read().decode())["tree"]["sha"]
full = json.loads(urllib.request.urlopen(urllib.request.Request("https://api.github.com/repos/%s/git/trees/%s?recursive=1" % (REPO, tree), headers=h), timeout=120).read().decode())
remote_blobs = {e["path"]: e["sha"] for e in full["tree"] if e["type"] == "blob"}
for rel in ("docs/WORKLOG.md", "tools/verify_v19_final.py", "tools/train_hybrid_final.py"):
    full_path = os.path.join(BASE, rel)
    if not os.path.exists(full_path):
        print(rel, "LOCAL_MISSING"); continue
    local_sha = subprocess.check_output([g, "-C", BASE, "hash-object", rel]).decode().strip()
    rsha = remote_blobs.get(rel)
    print("GIT_BLOB %-38s local=%s remote=%s match=%s" % (rel, local_sha[:12], (rsha or "MISSING")[:12], local_sha == rsha))
