# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "out", "overlay", "_p2d")
b = open(os.path.join(OUT, "build_log.txt"), "rb").read()
print("bytes", len(b))
print("head_hex", b[:32].hex())
print("nul_count", b.count(b"\x00"))
for enc in ("utf-16-le", "utf-16", "utf-8-sig", "gbk"):
    try:
        s = b.decode(enc)
        tail = s.strip().splitlines()[-6:]
        ascii_tail = ["".join(ch if 32 <= ord(ch) < 127 else " " for ch in l)[:150] for l in tail]
        print("ENC_OK", enc, "chars", len(s))
        for l in ascii_tail: print("   |", l)
        break
    except Exception as e:
        print("ENC_FAIL", enc, str(e)[:60])
