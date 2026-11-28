# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
t = open(os.path.join(BASE, "tools", "train_hybrid_cv.py"), encoding="utf-8").read()
# 1) 插入 warp6
if "def warp6" not in t:
    t = t.replace("def warp(img, cal, cx, cy):", """def warp6(img, cal, cx, cy):
    x0, y0 = cx - 2.5, cy - 2.5
    p = [cal.tile_to_px(x0,y0), cal.tile_to_px(x0+6,y0), cal.tile_to_px(x0+6,y0+6), cal.tile_to_px(x0,y0+6)]
    H = cv2.getPerspectiveTransform(np.float32(p), np.float32([[0,0],[S,0],[S,S],[0,S]]))
    return cv2.warpPerspective(img, H, (S,S), flags=cv2.INTER_AREA)
def warp(img, cal, cx, cy):""", 1)
# 2) 门控训练样本用 warp6
t = t.replace('gpos.append((warp(b["img"], b["cal"], gx, gy), 1))', 'gpos.append((warp6(b["img"], b["cal"], gx, gy), 1))', 1)
t = t.replace('gneg.append((warp(b["img"], b["cal"], cx, cy), 0))', 'gneg.append((warp6(b["img"], b["cal"], cx, cy), 0))', 1)
# 3) 评估：门控用 6x6，embedding 用 4x4
old = '''                xs = np.stack([warp(img, cal, cx, cy) for (cx,cy) in cs])[:,:,:,::-1].copy()
                x = torch.from_numpy(xs).permute(0,3,1,2).float().div(255).to(DEV)
                gp = torch.softmax(gate(x), 1)[:,1].cpu().numpy()
                e = emb(x).cpu().numpy()'''
new = '''                xs4 = np.stack([warp(img, cal, cx, cy) for (cx,cy) in cs])[:,:,:,::-1].copy()
                x4 = torch.from_numpy(xs4).permute(0,3,1,2).float().div(255).to(DEV)
                xs6 = np.stack([warp6(img, cal, cx, cy) for (cx,cy) in cs])[:,:,:,::-1].copy()
                x6 = torch.from_numpy(xs6).permute(0,3,1,2).float().div(255).to(DEV)
                gp = torch.softmax(gate(x6), 1)[:,1].cpu().numpy()
                e = emb(x4).cpu().numpy()'''
if old in t:
    t = t.replace(old, new, 1)
    t = t.replace('hybrid_report.json', 'hybrid_ctx_report.json')
    open(os.path.join(BASE, "tools", "train_hybrid_ctx_cv.py"), "w", encoding="utf-8", newline="\n").write(t)
    print("ctx script ok; warp6 count", t.count("warp6"))
else:
    print("eval anchor miss")
