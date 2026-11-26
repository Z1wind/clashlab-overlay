# -*- coding: utf-8 -*-
import json, re, urllib.request
def fetch(u):
    req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) clashlab"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()
def get_json(u):
    return json.loads(fetch(u).decode("utf-8", "ignore"))

bases = get_json("https://cocbases.com/wp-json/wp/v2/base?per_page=50")
print("bases:", len(bases))
sample = bases[0]
html = fetch(sample["link"]).decode("utf-8", "ignore")
print("post:", sample["link"], "html len", len(html))
imgs = sorted(set(re.findall(r'https://cocbases\.com/wp-content/uploads/[^"\'<> ]+\.(?:png|jpg|jpeg|webp)', html)))
print("imgs:", len(imgs))
for i in imgs[:8]:
    print("  ", i)
# th16 count
th16 = [b for b in bases if "town-hall-16" in " ".join(b.get("class_list") or [])]
print("th16 in first 50:", len(th16))
