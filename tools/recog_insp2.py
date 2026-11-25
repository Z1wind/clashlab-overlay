# -*- coding: utf-8 -*-
# recog_insp2.py — 查看 v6_stitched_base.png 全貌（缩略）+ 非黑区域包围盒
import os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(ROOT, "tools", "base_out")
p = os.path.join(ROOT, "out", "overlay", "v6_stitched_base.png")
im = cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_COLOR)
print("shape", im.shape)
gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
mask = gray > 8
ys, xs = np.where(mask)
print("bbox", xs.min(), ys.min(), xs.max(), ys.max())
# 非黑区按行带分块缩略，便于逐区看
h, w = im.shape[:2]
small = cv2.resize(im, (1400, int(h * 1400 / w)), interpolation=cv2.INTER_AREA)
cv2.imencode(".png", small)[1].tofile(os.path.join(OUT, "stitched_overview.png"))
# 把非黑 bbox 切成 3x2 六块放大存盘
x0, y0, x1, y1 = xs.min(), ys.min(), xs.max(), ys.max()
cw, ch = (x1 - x0) // 3, (y1 - y0) // 2
for r in range(2):
    for c in range(3):
        crop = im[y0 + r * ch:y0 + (r + 1) * ch, x0 + c * cw:x0 + (c + 1) * cw]
        cv2.imencode(".png", crop)[1].tofile(os.path.join(OUT, f"ov_r{r}c{c}.png"))
print("done")
