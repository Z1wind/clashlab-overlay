# -*- coding: utf-8 -*-
import os, json
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "war_base_montage.py")
t = open(p, encoding="utf-8").read()
if "json.dump" not in t:
    t = t.replace('''    made = montage(img, quad, items, prefix) if items else []
    return {"ok": True, "quad": quad.tolist(), "angle": ang, "items": len(items),''',
'''    made = montage(img, quad, items, prefix) if items else []
    meta_path = prefix + "_candidates.json"
    try:
        json.dump({"image": img_path, "quad": np.asarray(quad).tolist(), "items": items},
                  open(meta_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    except Exception:
        meta_path = None
    return {"ok": True, "quad": quad.tolist(), "angle": ang, "items": len(items), "meta": meta_path,''')
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("meta json writing added")
