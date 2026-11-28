# -*- coding: utf-8 -*-
"""给扫描器评估加：阈值扫描 + 距离去重 + F1 最优。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "train_tile_scanner.py")
t = open(p, encoding="utf-8").read()
old_start = t.index("        # 评估：全图扫描")
old_end = t.index("    mean = lambda k:")
new_eval = '''        # 评估：全图扫描 + 阈值扫描 + 距离去重
        net.eval()
        img, cal, blds = va["img"], va["cal"], va["blds"]
        gt = [(t, tx, ty) for (t, tx, ty, gx, gy) in blds]
        cells = [(cx, cy) for cx in range(2, 42) for cy in range(2, 42)]
        cand = []
        with torch.no_grad():
            for i in range(0, len(cells), 128):
                cs = cells[i:i+128]
                items = [(crop_at(img, cal, cx + .5, cy + .5), 0) for (cx, cy) in cs]
                x, _ = batch(items, False)
                prob = torch.softmax(net(x), 1)
                for k, (cx, cy) in enumerate(cs):
                    score, cls = float(prob[k, :NC-1].max()), int(prob[k, :NC-1].argmax())
                    cand.append((score, cls, cx + .5, cy + .5))
        best_f1 = None; best_t = None
        for th in (0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
            sel = sorted([c for c in cand if c[0] >= th], reverse=True)
            kept = []
            for c in sel:
                if all(abs(c[2]-q[2]) + abs(c[3]-q[3]) > 1.2 for q in kept): kept.append(c)
            matched = set(); tp = 0; type_ok = 0
            for p_ in kept:
                best = None
                for gi, (tt, tx, ty) in enumerate(gt):
                    if gi in matched: continue
                    d = abs(p_[2]-tx) + abs(p_[3]-ty)
                    if d < 1.6 and (best is None or d < best[0]): best = (d, gi)
                if best:
                    matched.add(best[1]); tp += 1
                    if types[p_[1]] == gt[best[1]][0]: type_ok += 1
            prec = tp / max(1, len(kept)); rec = tp / max(1, len(gt))
            f1 = 2*prec*rec / max(1e-9, prec+rec)
            if best_f1 is None or f1 > best_f1[0]:
                best_f1 = (f1, th, prec, rec, tp, len(kept), type_ok)
        f1, th, prec, rec, tp, npred, tok = best_f1
        tacc = tok / max(1, tp)
        print("hold base %d: gt=%d pred=%d tp=%d prec=%.3f recall=%.3f f1=%.3f type_acc=%.3f @th=%.2f" % (va["bi"], len(gt), npred, tp, prec, rec, f1, tacc, th), flush=True)
        reports.append({"base": va["bi"], "gt": len(gt), "pred": npred, "tp": tp, "prec": prec, "recall": rec, "f1": f1, "type_acc": tacc, "th": th})
'''
t = t[:old_start] + new_eval + t[old_end:]
t = t.replace('    print("MEAN prec=%.3f recall=%.3f type_acc=%.3f" % (mean("prec"), mean("recall"), mean("type_acc")))',
              '    print("MEAN prec=%.3f recall=%.3f f1=%.3f type_acc=%.3f" % (mean("prec"), mean("recall"), mean("f1"), mean("type_acc")))')
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("scanner eval patched")
