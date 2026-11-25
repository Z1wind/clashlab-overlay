# -*- coding: utf-8 -*-
# covmap.py — 链累积偏移 snap 到 (col,row) 网格，打印覆盖 ASCII，列=accX/440 行=accY/300
import json, os
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
log=json.load(open(os.path.join(ROOT,"out","overlay","blocks3","collect_log.json"),encoding="utf-8"))
items=[]; cx=cy=0.0
for t in log["tiles"]:
    cx+=t["dx"]; cy+=t["dy"]
    items.append((t["file"],round(cx/440,2),round(cy/300,2)))
# snap
cells={}
for f,x,y in items:
    c=int(round(x)); r=int(round(y))
    cells.setdefault((c,r),[]).append(f)
cs=[c for c,r in cells]; rs=[r for c,r in cells]
print("col",min(cs),max(cs),"row",min(rs),max(rs))
for r in range(max(rs),min(rs)-1,-1):
    line=f"r{r:>3} "
    for c in range(min(cs),max(cs)+1):
        line+=("## " if (c,r) in cells else ".. ")
    print(line)
# 打印每格文件名
for k,v in sorted(cells.items()):
    print(k,v)
