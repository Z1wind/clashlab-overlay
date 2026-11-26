# -*- coding: utf-8 -*-
import socket, urllib.request, os, json
print("env proxy:", {k: os.environ.get(k) for k in ("HTTP_PROXY","HTTPS_PROXY","ALL_PROXY","NO_PROXY")})
print("listening proxy-ish ports:")
for port in (7890, 7891, 7897, 10808, 10809, 1080, 8889):
    s = socket.socket(); s.settimeout(0.3)
    try:
        s.connect(("127.0.0.1", port)); print("  open:", port)
    except Exception:
        pass
    finally:
        s.close()

def probe(u, timeout=6):
    try:
        req = urllib.request.Request(u, method="HEAD", headers={"User-Agent": "clashlab"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status
    except Exception as e:
        return type(e).__name__ + ":" + str(e)[:40]

for u in ("https://api.github.com", "https://github.com", "https://raw.githubusercontent.com",
          "https://objects.githubusercontent.com", "https://api.trycloudflare.com",
          "https://bin.equinox.io", "https://pypi.org", "https://www.baidu.com"):
    print(u, "->", probe(u))
