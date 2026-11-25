# -*- coding: utf-8 -*-
# b14_adscan.py — 14号敌阵(kekejdj) 防空火箭定位：quad 网格叠加四象限3x巡片（新文件，不改旧脚本）
import os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EN = os.path.join(ROOT, "out", "overlay", "enemy")
SCRATCH = r"C:\Users\Admin（无密码）\AppData\Local\Doubao\User Data\Default\.doubao\agent_mode\workspace\.sessions\38455881728595202\agents\s_0007xvhw26c\scratch"
os.makedirs(SCRATCH, exist_ok=True)

buf = np.fromfile(os.path.join(EN, "b14_ov1.png"), dtype=np.uint8)
im = cv2.imdecode(buf, cv2.IMREAD_COLOR)
H0, W0 = im.shape[:2]

T = np.array([640., 58.]); R = np.array([1105., 325.]); B = np.array([640., 600.]); L = np.array([167., 308.])
src = np.float32([T, R, B, L])
dst = np.float32([(0, 0), (44, 0), (44, 44), (0, 44)])
Hpinv = cv2.getPerspectiveTransform(dst, src)  # platform -> ov1

def img_of(cr):
    v = np.array([cr[0], cr[1], 1.0])
    w = Hpinv @ v
    return w[:2] / w[2]

# 叠加平台网格（每4格一条细线，交点标格号）
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
        cv2.putText(grid, f"{c},{r}", tuple(p.astype(int)), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 0, 255), 1)

# b14_full 裁口 = ov1(195,88)-(1065,582)，四象限切分
CROP = (195, 88, 1065, 582)
regions = {
    "nw": (195, 88, 630, 335),
    "ne": (630, 88, 1065, 335),
    "sw": (195, 335, 630, 582),
    "se": (630, 335, 1065, 582),
}
z = 3.0
for name, (x0, y0, x1, y1) in regions.items():
    c = grid[y0:y1, x0:x1]
    big = cv2.resize(c, None, fx=z, fy=z, interpolation=cv2.INTER_CUBIC)
    out = os.path.join(SCRATCH, f"b14_scan_{name}.png")
    cv2.imencode(".png", big)[1].tofile(out)
    print(name, (x0, y0, x1, y1), big.shape)
