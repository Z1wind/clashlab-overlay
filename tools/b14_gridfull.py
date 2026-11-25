# -*- coding: utf-8 -*-
# b14_gridfull.py — 全 ov1 平台网格标注图（每2格细线/每4格标号），供人工读格位（新文件）
import os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EN = os.path.join(ROOT, "out", "overlay", "enemy")
SCRATCH = r"C:\Users\Admin（无密码）\AppData\Local\Doubao\User Data\Default\.doubao\agent_mode\workspace\.sessions\38455881728595202\agents\s_0007xvhw26c\scratch"
buf = np.fromfile(os.path.join(EN, "b14_ov1.png"), dtype=np.uint8)
im = cv2.imdecode(buf, cv2.IMREAD_COLOR)
T = np.array([640., 58.]); R = np.array([1105., 325.]); B = np.array([640., 600.]); L = np.array([167., 308.])
src = np.float32([T, R, B, L]); dst = np.float32([(0, 0), (44, 0), (44, 44), (0, 44)])
Hpinv = cv2.getPerspectiveTransform(dst, src)
def img_of(cr):
    v = np.array([cr[0], cr[1], 1.0]); w = Hpinv @ v
    return w[:2] / w[2]
grid = im.copy()
for c in range(0, 45, 2):
    p0 = img_of((c, 0)); p1 = img_of((c, 44))
    cv2.line(grid, tuple(p0.astype(int)), tuple(p1.astype(int)), (0, 220, 220), 1)
for r in range(0, 45, 2):
    p0 = img_of((0, r)); p1 = img_of((44, r))
    cv2.line(grid, tuple(p0.astype(int)), tuple(p1.astype(int)), (0, 220, 220), 1)
for c in range(0, 45, 4):
    for r in range(0, 45, 4):
        p = img_of((c, r))
        cv2.putText(grid, f"{c},{r}", tuple(p.astype(int)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 255), 1)
big = cv2.resize(grid, None, fx=1.6, fy=1.6, interpolation=cv2.INTER_CUBIC)
cv2.imencode(".png", big)[1].tofile(os.path.join(SCRATCH, "b14_gridfull.png"))
print(big.shape)
