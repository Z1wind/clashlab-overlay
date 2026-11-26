# -*- coding: utf-8 -*-
import urllib.request
def probe(u, timeout=8):
    try:
        req = urllib.request.Request(u, method="HEAD", headers={"User-Agent": "clashlab"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status
    except Exception as e:
        return type(e).__name__ + ":" + str(e)[:50]
for u in ("https://dl.google.com/android/repository/repository2-1.xml",
          "https://dl.google.com/android/repository/commandlinetools-win-11076708_latest.zip",
          "https://services.gradle.org/distributions/",
          "https://repo1.maven.org/maven2/",
          "https://download.java.net/",
          "https://adoptium.net/"):
    print(u, "->", probe(u))
