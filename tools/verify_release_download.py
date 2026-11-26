# -*- coding: utf-8 -*-
import hashlib, os, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
URL = "https://github.com/Z1wind/clashlab-overlay/releases/download/backup-2026-11-26/clashlab_annotated_20261126.zip"
print("GET", URL)
with urllib.request.urlopen(urllib.request.Request(URL, headers={"User-Agent": "clashlab"}), timeout=120) as r:
    data = r.read()
    print("HTTP", r.status, "Content-Length", r.headers.get("Content-Length"), "bytes", len(data))
print("remote md5:", hashlib.md5(data).hexdigest())
local = open(r"out\backup\clashlab_annotated_20261126.zip", "rb").read()
print("local  md5:", hashlib.md5(local).hexdigest(), "match:", hashlib.md5(local).hexdigest() == hashlib.md5(data).hexdigest())
