# -*- coding: utf-8 -*-
"""探测 OpenLayout id 二进制格式。"""
import base64, json, re, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read().decode("utf-8", "ignore")
def get_link(html):
    m = re.search(r"OpenLayout&id=([^\"&]+)", html)
    return m.group(1) if m else None
for pid in (138, 143):
    html = fetch("https://clashofclans-layouts.com/plans/th_16/war_%d.html" % pid)
    link = get_link(html)
    print("war_%d link:" % pid, link)
    if not link:
        continue
    raw = link.split(":")[2]
    pad = "=" * (-len(raw) % 4)
    data = base64.urlsafe_b64decode(raw + pad)
    print(" bytes:", len(data), "hex head:", data[:64].hex(" "))
    print(" ascii:", data[:120])
