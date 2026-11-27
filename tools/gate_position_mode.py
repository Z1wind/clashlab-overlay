# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"

# 1) auto_candidates: gate_only 模式
p = os.path.join(BASE, "clashlab", "auto_candidates.py")
t = open(p, encoding="utf-8").read()
if "gate_only" not in t:
    t = t.replace("def candidates(image_path, quad, max_n=30, min_conf=0.97, min_var=60.0):",
                  "def candidates(image_path, quad, max_n=30, min_conf=0.97, min_var=60.0, gate_only=False):")
    old = '''        if not picked_warps:
            continue
        for i in range(0, len(picked_warps), 512):'''
    new = '''        if not picked_warps:
            continue
        if gate_only:
            # 只给「建筑位置」，类型由用户点选
            for (x, y), prob in zip(picked_tiles, [gp[j] for j in keep] if gate else [1.0] * len(picked_tiles)):
                items.append({"tile": [x, y], "size": size, "gate_conf": round(float(prob), 4)})
            continue
        for i in range(0, len(picked_warps), 512):'''
    if old in t:
        t = t.replace(old, new, 1)
        t = t.replace('''    return {"ok": True, "items": picked, "total_before_dedupe": len(items),''',
                      '''    if gate_only:
        for it in items:
            it.setdefault("type", None)
    return {"ok": True, "items": picked, "gate_only": bool(gate_only), "total_before_dedupe": len(items),''')
        open(p, "w", encoding="utf-8", newline="\n").write(t)
        print("gate_only added")
    else:
        print("loop anchor miss")

# 2) annotator /candidates 传 gate_only + /save manifest
p2 = os.path.join(BASE, "clashlab", "annotator.py")
t2 = open(p2, encoding="utf-8").read()
if "gate_only" not in t2:
    t2 = t2.replace('res = _ac.candidates(STATE.get("image"), quad, max_n=int(doc.get("max_n") or 30))',
                    'res = _ac.candidates(STATE.get("image"), quad, max_n=int(doc.get("max_n") or 30),\n                                         gate_only=bool(doc.get("gate_only")))')
    # manifest 落盘
    t2 = t2.replace('''        try:
            shown = os.path.relpath(path, ROOT)''',
'''        try:
            manifest = os.path.join(out_dir, "_train_manifest.jsonl")
            with open(manifest, "a", encoding="utf-8") as mf:
                mf.write(json.dumps({"name": name, "image": STATE.get("image"),
                                     "buildings": len(doc.get("buildings") or []),
                                     "walls": len(doc.get("walls") or []),
                                     "quad": doc.get("quad"), "saved_at": __import__("time").strftime("%Y-%m-%dT%H:%M:%S")},
                                    ensure_ascii=False) + "\\n")
        except Exception:
            pass
        try:
            shown = os.path.relpath(path, ROOT)''')
    open(p2, "w", encoding="utf-8", newline="\n").write(t2)
    print("annotator gate_only + manifest")

# 3) 页面：自动候选改为位置候选，点击落位
if 'gate_only' not in t2:
    pass
t2 = open(p2, encoding="utf-8").read()
if "位置候选" not in t2:
    t2 = t2.replace('<button id="candbtn" title="实验性：torch 分类器候选">自动候选</button>',
                    '<button id="candbtn" title="门控模型给建筑位置，类型用当前选中">位置候选</button>')
    t2 = t2.replace('body:JSON.stringify({quad:corners,max_n:30})',
                    'body:JSON.stringify({quad:corners,max_n:40,gate_only:true})')
    t2 = t2.replace('document.getElementById(\'report\').textContent=\'实验候选 \'+cands.length+\' 个（离开角、点选接受；点击确定后人工核对）\';',
                    'document.getElementById(\'report\').textContent=\'位置候选 \'+cands.length+\' 个：先选类型再点蓝框落位\';')
    # 点击落位：cands 项无 type -> 用当前 sel
    t2 = t2.replace("buildings.push({type:cd.type, tile:cd.tile}); cands.splice(ci,1); saveDraft(); st(); return; } }",
                    "buildings.push({type: sel, tile:cd.tile}); cands.splice(ci,1); saveDraft(); st(); return; } }")
    t2 = t2.replace("ctx.putText", "ctx.fillText")
    open(p2, "w", encoding="utf-8", newline="\n").write(t2)
    print("page position candidates")
