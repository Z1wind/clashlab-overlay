# -*- coding: utf-8 -*-
import sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
for u in ("https://clashk.ing", "https://clashk.ing/bases", "https://clashk.ing/base",
          "https://www.clashk.ing", "https://api.clashk.ing", "https://clashk.ing/en/bases"):
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 clashlab"}), timeout=20)
        b = r.read().decode("utf-8", "ignore")
        title = b.split("<title>")[1].split("</title>")[0][:80] if "<title>" in b else ""
        print(u, r.status, len(b), "| title:", title)
    except Exception as e:
        print(u, "ERR", type(e).__name__, str(e)[:70])
