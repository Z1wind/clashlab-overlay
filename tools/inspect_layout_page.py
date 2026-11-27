# -*- coding: utf-8 -*-
"""在阵图页面里找内嵌布局数据（JS 变量/JSON/坐标）。"""
import re, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
url = "https://clashofclans-layouts.com/plans/th_16/war_138.html"
html = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read().decode("utf-8", "ignore")
print("len", len(html))
for kw in ("var ", "JSON", "buildings", "grid", "layout", "coords", "points", "data-", "canvas", "svg", "tiles"):
    idxs = [m.start() for m in re.finditer(re.escape(kw), html)][:3]
    print(kw, "count", html.count(kw), "first idx", idxs)
# 找 <script> 内容和长数字数组
scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, re.S)
print("scripts:", len(scripts))
for i, s in enumerate(scripts[:8]):
    print("--- script", i, "len", len(s), "---")
    print(s[:300].replace("\n", " ")[:300])
# 找像坐标数组的片段
cand = re.findall(r"\[\s*\d{1,2}\s*,\s*\d{1,2}\s*\]", html)
print("coord-like pairs:", len(cand), cand[:15])
