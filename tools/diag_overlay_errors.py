# -*- coding: utf-8 -*-
import os, re, sys, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
log = open(os.path.join(ROOT, "out", "overlay", "overlay.log"), "r", encoding="utf-8", errors="replace")
lines = log.readlines()[-400:]
errs = collections.Counter()
for ln in lines:
    m = re.search(r"(error|Exception|Traceback|失败|错误|missing|not found|NameError|KeyError|AttributeError)", ln)
    if m:
        key = re.sub(r"\d+", "N", ln.strip())[:110]
        errs[key] += 1
print("log tail lines:", len(lines))
for k, v in errs.most_common(15):
    print(v, "|", k)
print("--- panel rect lines ---")
for ln in lines[-40:]:
    if "rect=" in ln or "attach" in ln or "target" in ln:
        print(ln.strip()[:120])
