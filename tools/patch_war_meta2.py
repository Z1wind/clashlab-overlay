# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "war_base_montage.py")
t = open(p, encoding="utf-8").read()
old = '''    made = montage(img, quad, items, prefix) if items else []
    return {"ok": True, "quad": quad.tolist(), "angle": ang, "items": len(items),
            "montages": [os.path.basename(m) for m in made],
            "meta": os.path.join(outdir, name + "_candidates.json")}'''
new = '''    made = montage(img, quad, items, prefix) if items else []
    meta_path = prefix + "_candidates.json"
    try:
        import json as _json
        _json.dump({"image": img_path, "quad": np.asarray(quad).tolist(), "items": items},
                   open(meta_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    except Exception:
        meta_path = None
    return {"ok": True, "quad": quad.tolist(), "angle": ang, "items": len(items),
            "montages": [os.path.basename(m) for m in made], "meta": meta_path}'''
if old in t:
    t = t.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("process meta dump written")
else:
    print("anchor miss")
