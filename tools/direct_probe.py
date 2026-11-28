# -*- coding: utf-8 -*-
import sys, ssl, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
try:
    with op.open("https://api.github.com/", timeout=25) as r:
        print("DIRECT_OK", r.status, r.headers.get("server"))
except Exception as e:
    print("DIRECT_FAIL", repr(e)[:200])
