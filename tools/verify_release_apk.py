# -*- coding: utf-8 -*-
import hashlib, json, os, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
URL = "https://github.com/Z1wind/clashlab-overlay/releases/download/v0.3.0/ClashLabAnnotator.apk"
print("GET", URL)
with urllib.request.urlopen(urllib.request.Request(URL, headers={"User-Agent": "clashlab"}), timeout=180) as r:
    data = r.read()
    print("HTTP", r.status, "Content-Length", r.headers.get("Content-Length"), "bytes", len(data))
local = open(r"dist\ClashLabAnnotator.apk", "rb").read()
print("remote md5:", hashlib.md5(data).hexdigest())
print("local  md5:", hashlib.md5(local).hexdigest(), "match:", hashlib.md5(local).hexdigest() == hashlib.md5(data).hexdigest())
