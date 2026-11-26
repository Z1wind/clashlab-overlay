# -*- coding: utf-8 -*-
import re, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
base = "https://clashk.ing"
html = urllib.request.urlopen(urllib.request.Request(base, headers={"User-Agent": "Mozilla/5.0"}), timeout=20).read().decode("utf-8", "ignore")
scripts = re.findall(r'src="([^"]+\.js[^"]*)"', html)
print("scripts:", scripts[:8])
for s in scripts[:6]:
    url = s if s.startswith("http") else base + s
    try:
        js = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=25).read().decode("utf-8", "ignore")
    except Exception as e:
        print(url, "ERR", str(e)[:60]); continue
    hits = sorted(set(re.findall(r"/v2/[a-zA-Z0-9/{}$._-]+", js)))
    print(url, "len", len(js), "| /v2:", hits[:15])
    print("   bases:", js.count("bases"), "layout:", js.count("layout"))
