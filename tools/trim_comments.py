# -*- coding: utf-8 -*-
"""压缩「连续 >=3 行的整行注释块」为标准 1 行（只保留首行），减少注释墙；不改任何代码。"""
import io, os, sys

TARGETS = sys.argv[1:]
def compress(path):
    lines = open(path, encoding="utf-8").read().splitlines()
    out, i, removed = [], 0, 0
    while i < len(lines):
        line = lines[i]
        if line.lstrip().startswith("#") and not line.lstrip().startswith(("#!", "# -*-")):
            j = i
            block = []
            while j < len(lines) and lines[j].lstrip().startswith("#") and not lines[j].lstrip().startswith(("#!", "# -*-")):
                block.append(lines[j]); j += 1
            if len(block) >= 3:
                out.append(block[0]); removed += len(block) - 1
            else:
                out.extend(block)
            i = j
        else:
            out.append(line); i += 1
    open(path, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
    print("%-40s -%d lines" % (os.path.basename(path), removed))

for t in TARGETS:
    if os.path.exists(t):
        compress(t)
