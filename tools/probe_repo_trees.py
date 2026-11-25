# -*- coding: utf-8 -*-
import json, urllib.request

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 clashlab"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))

repos = [
    ("rishi-ragavan/Viking--Clash_of_Clans_base-optimizer", "main"),
    ("laurentDellaNegra/coc-layout-ai", "main"),
    ("Peter537/clash-of-clans-base-validator", "main"),
    ("Wire15/clash-buddy", "main"),
]
for repo, br in repos:
    for branch in (br, "master"):
        try:
            data = get("https://data.jsdelivr.com/v1/packages/gh/%s@%s?structure=flat" % (repo, branch))
            files = [f["name"] for f in data.get("files", [])]
            print("==", repo, branch, "files:", len(files))
            interesting = [f for f in files if any(k in f.lower() for k in
                          ("layout", "json", "base", "village", "data", ".png", ".jpg"))]
            for f in interesting[:25]:
                print("   ", f)
            break
        except Exception as e:
            print("ERR", repo, branch, str(e)[:70])
