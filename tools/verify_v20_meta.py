# -*- coding: utf-8 -*-
import hashlib, json, os, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))
TOKEN = os.environ["GH_TOKEN"]; REPO = "Z1wind/clashlab-overlay"
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
NAME = "ClashLabAnnotator_Desktop_v2.0.exe"
LOCAL = os.path.join(BASE, "dist", NAME)
data = open(LOCAL, "rb").read()
print("LOCAL", NAME, len(data), "bytes", "md5", hashlib.md5(data).hexdigest().upper())
h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
rels = json.loads(urllib.request.urlopen(urllib.request.Request("https://api.github.com/repos/%s/releases?per_page=20" % REPO, headers=h), timeout=120).read().decode())
rel = next(x for x in rels if x["tag_name"] == "v0.3.7")
a = next(x for x in rel["assets"] if x["name"] == NAME)
print("REMOTE", a["name"], a["size"], "state=" + a["state"], "updated_at=" + a["updated_at"], "digest=" + str(a.get("digest")))
print("SIZE_MATCH", a["size"] == len(data))
