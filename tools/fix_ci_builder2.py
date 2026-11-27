# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "build_apk_ci.py")
t = open(p, encoding="utf-8").read()
old = '''    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if p.returncode != 0:
        print((p.stdout or "")[-2000:]); print((p.stderr or "")[-3000:])
        raise SystemExit("FAILED (%d)" % p.returncode)
    return p'''
new = '''    p = subprocess.run(cmd, cwd=cwd, capture_output=True)
    out = (p.stdout or b"").decode("utf-8", "replace")
    err = (p.stderr or b"").decode("utf-8", "replace")
    if p.returncode != 0:
        print(out[-2000:]); print(err[-3000:])
        raise SystemExit("FAILED (%d)" % p.returncode)
    return p'''
if old in t:
    t = t.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("run() bytes-safe")
else:
    print("anchor miss")
