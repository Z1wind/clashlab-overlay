# -*- coding: utf-8 -*-
import sys, urllib.request, socket
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
for url in ("https://api.github.com/", "https://github.com/", "https://objects.githubusercontent.com/"):
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            print(url, "OK", r.status)
    except Exception as e:
        print(url, "FAIL", repr(e)[:160])
