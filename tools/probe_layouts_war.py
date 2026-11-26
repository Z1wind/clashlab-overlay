# -*- coding: utf-8 -*-
import glob, json, os, sys, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
print("--- layout files ---")
for pat in ("bases/**/layout.json", "layouts/*.json", "out/annotate/*_annotated.json", "out/annotate/*_quad.json"):
    fs = glob.glob(os.path.join(BASE, pat), recursive=True)
    print(pat, len(fs))
    for f in fs[:12]:
        print("   ", os.path.relpath(f, BASE), os.path.getsize(f))
print("--- clashking base paths ---")
try:
    paths = json.load(open(os.path.join(BASE, "out", "clashking_paths.json"), encoding="utf-8"))
    pl = paths if isinstance(paths, list) else list(paths.keys())
    for p in pl:
        if "base" in str(p).lower():
            print("  ", p)
except Exception as e:
    print("paths err", e)
def get(u):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "clashlab"}), timeout=20) as r:
            return r.status, r.read().decode("utf-8", "ignore")[:300]
    except Exception as e:
        return "ERR", type(e).__name__ + ":" + str(e)[:70]
for u in ("https://api.clashk.ing/v2/bases/personal?playerTag=%23QCRJPL2RJ",
          "https://api.clashk.ing/v2/bases/personal?tag=%23QCRJPL2RJ",
          "https://api.clashk.ing/v2/bases/personal"):
    print(u, "->", get(u))
