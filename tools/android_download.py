# -*- coding: utf-8 -*-
"""下载 Android 构建依赖到 E 盘（JDK17 + cmdline-tools）。"""
import os, sys, time, urllib.request

DEST = r"E:\tools\android-setup"
os.makedirs(DEST, exist_ok=True)
ITEMS = [
    ("jdk17.zip", "https://api.adoptium.net/v3/binary/latest/17/ga/windows/x64/jdk/hotspot/normal/eclipse?project=jdk"),
    ("cmdline-tools.zip", "https://dl.google.com/android/repository/commandlinetools-win-11076708_latest.zip"),
]

def dl(name, url, retries=3):
    dst = os.path.join(DEST, name)
    if os.path.exists(dst) and os.path.getsize(dst) > 30_000_000:
        print("[skip]", name, os.path.getsize(dst)); return dst
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "clashlab-setup"})
            t0 = time.time()
            with urllib.request.urlopen(req, timeout=120) as r, open(dst + ".part", "wb") as f:
                total = int(r.headers.get("Content-Length") or 0)
                got = 0
                while True:
                    chunk = r.read(1 << 20)
                    if not chunk:
                        break
                    f.write(chunk); got += len(chunk)
                    if total and got % (20 << 20) < (1 << 20):
                        print("  %s %d/%d MB (%.0fs)" % (name, got // (1 << 20), total // (1 << 20), time.time() - t0), flush=True)
            os.replace(dst + ".part", dst)
            print("[downloaded]", name, os.path.getsize(dst), "bytes", flush=True)
            return dst
        except Exception as e:
            print("[retry %d] %s: %r" % (attempt, name, e), flush=True)
            time.sleep(2)
    raise SystemExit("download failed: " + name)

for name, url in ITEMS:
    dl(name, url)
print("ALL_DONE")
