# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
# 1) 支持每条样本自己的 quad
p = os.path.join(BASE, "tools", "finetune_shot_type.py")
t = open(p, encoding="utf-8").read()
t = t.replace('''    quad = np.float32(doc["quad"])''', '''    quad = np.float32(doc["quad"]) if doc.get("quad") else None''')
t = t.replace('''        if p not in imgs:
            im = cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)
            imgs[p] = (im, Calib.from_quad(quad, n=44))''',
'''        q = np.float32(it.get("quad") or quad)
        key = (p, tuple(map(tuple, q.tolist())))
        if key not in imgs:
            im = cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)
            imgs[key] = (im, Calib.from_quad(q, n=44))''')
t = t.replace('''        im, cal = imgs[p]''', '''        im, cal = imgs[key]''')
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("per-item quad support")

# 2) 用 5 张图纸标注生成测试 labels
import json, re
items = []
MAP = {"01_annotated.json": "war_138.jpg", "03_annotated.json": "war_143.jpg",
       "04_annotated.json": "war_141.jpg", "05_annotated.json": "war_139.jpg",
       "06_annotated.json": "defence_17.jpg"}
for ann_name, img_name in MAP.items():
    ann = json.load(open(os.path.join(BASE, "out", "annotate", ann_name), encoding="utf-8"))
    m = re.search(r"quad=\[\[([^\]]+)\],\[([^\]]+)\],\[([^\]]+)\],\[([^\]]+)\]\]", ann.get("note") or "")
    if not m:
        continue
    quad = [[float(x) for x in g.split(",")] for g in m.groups()]
    for b in ann.get("buildings") or []:
        items.append({"image": os.path.join(BASE, "out", "layouts_src", img_name),
                      "quad": quad, "tile": b.get("tile"), "size": 2, "type": b.get("type")})
doc = {"items": items}
out = os.path.join(BASE, "out", "labels", "render_test_labels.json")
json.dump(doc, open(out, "w", encoding="utf-8"), ensure_ascii=False)
print("test labels:", len(items), "->", out)
