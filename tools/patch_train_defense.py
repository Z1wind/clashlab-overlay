# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "train_save_model.py")
t = open(p, encoding="utf-8").read()
if "--only-defense" in t:
    print("already patched")
else:
    t = t.replace('    ap.add_argument("--threads", type=int, default=0)',
                  '    ap.add_argument("--threads", type=int, default=0)\n'
                  '    ap.add_argument("--only-defense", action="store_true",\n'
                  '                    help="只用防御类样本（assets.STATS + TH16_OVERRIDE），去掉经济/兵营/陷阱")')
    old = '''    crops, labels, bases = build_dataset(files)
    if not crops:
        raise SystemExit("build_dataset 返回空（layout 缺 quad 或 base.png 缺失）")
'''
    new = '''    crops, labels, bases = build_dataset(files)
    if not crops:
        raise SystemExit("build_dataset 返回空（layout 缺 quad 或 base.png 缺失）")
    if a.only_defense:
        from clashlab import assets as _assets
        keep = set(_assets.STATS) | set(getattr(_assets, "TH16_OVERRIDE", {}))
        idx = [i for i, lb in enumerate(labels) if lb in keep]
        dropped = len(labels) - len(idx)
        crops = [crops[i] for i in idx]
        labels = [labels[i] for i in idx]
        bases = [bases[i] for i in idx]
        print("[filter] only-defense keep=%d dropped=%d" % (len(idx), dropped), flush=True)
'''
    if old in t:
        t = t.replace(old, new, 1)
        open(p, "w", encoding="utf-8", newline="\n").write(t)
        print("train script patched")
    else:
        print("anchor miss")
