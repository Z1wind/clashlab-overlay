# -*- coding: utf-8 -*-
import collections, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
lines = open(ROOT + r"\out\overlay\overlay.log", "r", encoding="utf-8", errors="replace").readlines()
tail = lines[-20000:]
pat = re.compile(r"(error|Error|Exception|Traceback|失败|错误|无法|missing|not found|NameError|KeyError|AttributeError|401|403|500)")
count = collections.Counter()
for ln in tail:
    if pat.search(ln):
        s = ln.strip()
        s = re.sub(r"\d{2}:\d{2}:\d{2}", "HH:MM:SS", s)
        s = re.sub(r"\d+", "N", s)
        count[s[:120]] += 1
print("log lines examined:", len(tail), "| error-like:", sum(count.values()))
for k, v in count.most_common(20):
    print("%4d | %s" % (v, k))
