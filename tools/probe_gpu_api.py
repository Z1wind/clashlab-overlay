# -*- coding: utf-8 -*-
import re, urllib.request
def html(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "c"}), timeout=30).read().decode("utf-8", "ignore")
h = html("https://download.pytorch.org/whl/cu126/torch/")
vers = sorted(set(re.findall(r"torch-([0-9.]+)%2Bcu126-cp313-cp313-win_amd64", h)))
print("cu126 cp313 all:", vers)
print("has 2.15:", [v for v in vers if v.startswith("2.15")])
print("---- ClashKing API probes ----")
def get(u):
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "clashlab"})
        with urllib.request.urlopen(req, timeout=15) as r:
            b = r.read().decode("utf-8", "ignore")
            return r.status, b[:260].replace("\n", " ")
    except Exception as e:
        return "ERR", type(e).__name__ + ":" + str(e)[:70]
for u in ("https://api.clashk.ing/",
          "https://api.clashk.ing/health",
          "https://api.clashk.ing/player/8Q",
          "https://api.clashk.ing/v1/player/8Q",
          "https://api.clashk.ing/api/player/8Q"):
    print(u, "->", get(u))
