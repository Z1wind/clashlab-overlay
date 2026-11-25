# -*- coding: utf-8 -*-
"""看别人项目的抓取/布局生成代码，判断有没有「坐标来源」。"""
import urllib.request

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 clashlab"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode("utf-8", "ignore")

files = {
    "viking/scraper.py": "https://raw.githubusercontent.com/rishi-ragavan/Viking--Clash_of_Clans_base-optimizer/main/data_collection/scraper.py",
    "viking/generate_layout_json.py": "https://raw.githubusercontent.com/rishi-ragavan/Viking--Clash_of_Clans_base-optimizer/main/model_training/generate_layout_json.py",
    "viking/render_base.py": "https://raw.githubusercontent.com/rishi-ragavan/Viking--Clash_of_Clans_base-optimizer/main/model_training/render_base.py",
    "layout-ai/model.ts": "https://raw.githubusercontent.com/laurentDellaNegra/coc-layout-ai/main/src/model/layout.ts",
}
for name, u in files.items():
    try:
        txt = get(u)
        print("=" * 25, name, len(txt), "lines", txt.count("\n") + 1)
        print(txt[:1400].replace("\r", ""))
    except Exception as e:
        print(name, "ERR", str(e)[:80])
