# -*- coding: utf-8 -*-
import re, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
js = urllib.request.urlopen(urllib.request.Request("https://clashk.ing/assets/index-DFv_12UA.js",
    headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read().decode("utf-8", "ignore")
for m in re.finditer("bases", js):
    i = m.start()
    seg = js[max(0, i-90):i+120].replace("\n", " ")
    print("...", seg[:210])
print("---- layout contexts ----")
for m in list(re.finditer("layout", js))[:6]:
    i = m.start()
    print("...", js[max(0, i-90):i+120].replace("\n", " ")[:210])
