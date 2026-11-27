# -*- coding: utf-8 -*-
"""探测 OpenLayout id 二进制格式（处理 URL 编码）。"""
import base64, re, sys, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read().decode("utf-8", "ignore")
def get_link(html):
    m = re.search(r"OpenLayout&id=([^\"&]+)", html)
    return urllib.parse.unquote(m.group(1)) if m else None
for pid in (138, 143):
    html = fetch("https://clashofclans-layouts.com/plans/th_16/war_%d.html" % pid)
    link = get_link(html)
    print("war_%d link:" % pid, link)
    if not link:
        continue
    parts = link.split(":")
    print(" parts:", parts[:2], "| payload chars:", len(parts[2]) if len(parts) > 2 else 0)
    raw = parts[2]
    data = base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4))
    print(" bytes:", len(data))
    print(" hex head:", data[:80].hex(" "))
    # 尝试 utf-8 可读部分
    printable = "".join(chr(b) if 32 <= b < 127 else "." for b in data[:160])
    print(" ascii:", printable)
