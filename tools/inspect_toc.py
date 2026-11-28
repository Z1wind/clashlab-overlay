# -*- coding: utf-8 -*-
import ast, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
path = os.path.join(BASE, "build_exe", "ClashLabAnnotator", "Analysis-00.toc")
txt = open(path, encoding="utf-8", errors="replace").read()
tree = ast.parse(txt)
items = []
def walk(node):
    if isinstance(node, (ast.Tuple, ast.List)):
        for el in node.elts:
            walk(el)
    elif isinstance(node, ast.Constant) and isinstance(node.value, str):
        p = node.value
        if os.path.isfile(p):
            try: items.append((os.path.getsize(p), p))
            except Exception: pass
walk(tree)
seen = set(); uniq = []
for sz, p in items:
    if p in seen: continue
    seen.add(p); uniq.append((sz, p))
uniq.sort(reverse=True)
total = sum(sz for sz, _ in uniq)
print("files", len(uniq), "total GB", round(total/1e9, 2))
for sz, p in uniq[:15]:
    print("%.1f MB  %s" % (sz/1e6, p[-120:]))
