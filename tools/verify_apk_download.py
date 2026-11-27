# -*- coding: utf-8 -*-
import hashlib, os, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
dst = os.path.join(BASE, "out", "live", "apk_download.apk")
url = "https://github.com/Z1wind/clashlab-overlay/releases/download/v0.3.0/ClashLabAnnotator.apk"
p = subprocess.run(["curl.exe", "-s", "-L", "--max-time", "180",
                    "-w", "HTTP=%{http_code} SIZE=%{size_download}", "-o", dst, url],
                   capture_output=True, text=True)
print("curl:", p.stdout.strip()[:120], "| rc", p.returncode)
if os.path.exists(dst):
    remote = open(dst, "rb").read()
    local = open(os.path.join(BASE, "dist", "ClashLabAnnotator.apk"), "rb").read()
    print("remote bytes", len(remote), "md5", hashlib.md5(remote).hexdigest())
    print("local  bytes", len(local), "md5", hashlib.md5(local).hexdigest())
    print("match:", hashlib.md5(local).hexdigest() == hashlib.md5(remote).hexdigest())
