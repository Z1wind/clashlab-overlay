# -*- coding: utf-8 -*-
"""诚实 CV：混合 + 位置精修（±0.25 格，门控概率最大化）。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
src = os.path.join(BASE, "tools", "train_hybrid_cv.py")
t = open(src, encoding="utf-8").read()
old = """        best = None
        for gth in (0.5,0.6,0.7,0.8,0.9):"""
new = """        # ---- 位置精修：对候选在 ±0.25 格内用门控概率最大化 ----
        def refine_center(cx, cy):
            best = (0.0, cx, cy)
            g0 = gprob_map.get((int(cx-.5), int(cy-.5)))
            best = (g0 if g0 is not None else 0.0, cx, cy)
            for dx in (-0.25, 0.0, 0.25):
                for dy in (-0.25, 0.0, 0.25):
                    if dx == 0.0 and dy == 0.0: continue
                    xx, yy = cx+dx, cy+dy
                    c = warp_gray(img, cal, xx-.5, yy-.5, S)
                    xs = np.stack([c])[:,:,:,None].repeat(3,3)[:,:,:,::-1].copy()
                    x = torch.from_numpy(xs).permute(0,3,1,2).float().div(255).to(DEV)
                    gp = float(torch.softmax(gate(x),1)[0,1])
                    if gp > best[0]: best = (gp, xx, yy)
            return best[1], best[2]
        refine_map = {}
        for cell, (g, e) in gprob_map.items() if False else []:
            pass
        best = None
        for gth in (0.5,0.6,0.7,0.8,0.9):"""
if old in t:
    t = t.replace(old, new, 1)
    # 在 kept 收集前对 cand 做精修
    old2 = """            cand.sort(reverse=True)
            for eth in (0.6,0.7,0.8,0.85):"""
    new2 = """            cand.sort(reverse=True)
            refined = []
            for (bs, idx, cx, cy) in cand[:140]:
                rx, ry = refine_center(cx, cy)
                refined.append((bs, idx, rx, ry))
            cand = refined
            for eth in (0.6,0.7,0.8,0.85):"""
    t = t.replace(old2, new2, 1)
    t = t.replace('hybrid_report.json', 'hybrid_refine_report.json')
    open(os.path.join(BASE, "tools", "train_hybrid_refine_cv.py"), "w", encoding="utf-8", newline="\n").write(t)
    print("refine CV script written")
else:
    print("anchor miss")
