# -*- coding: utf-8 -*-
# v9 复核：弹道条带(Q(235,458)->(795,443)) 3x 裁片，逐栋核对类型；带像素刻度
import cv2, numpy as np, os
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
SCRATCH = r"C:\Users\Admin（无密码）\AppData\Local\Doubao\User Data\Default\.doubao\agent_mode\workspace\.sessions\38455881728595202\agents\s_0007xvhw26c\scratch"
buf = np.fromfile(os.path.join(ROOT, "out", "overlay", "v6_l0_three_shot_base.png"), dtype=np.uint8)
im = cv2.imdecode(buf, cv2.IMREAD_COLOR)
z = 3.0
# 条带分三段，覆盖整条射线
crops = {
    "seg1": (150, 400, 360, 540),
    "seg2": (340, 400, 560, 540),
    "seg3": (540, 390, 820, 530),
}
for name, (x0, y0, x1, y1) in crops.items():
    c = im[y0:y1, x0:x1]
    big = cv2.resize(c, None, fx=z, fy=z, interpolation=cv2.INTER_CUBIC)
    bh, bw = big.shape[:2]
    for gx in range(x0 // 12 * 12, x1, 12):
        u = int((gx - x0) * z)
        cv2.line(big, (u, 0), (u, bh), (0, 0, 255), 1)
        if gx % 24 == 0:
            cv2.putText(big, str(gx), (u + 2, 11), cv2.FONT_HERSHEY_SIMPLEX, 0.32, (0, 0, 255), 1)
    for gy in range(y0 // 12 * 12, y1, 12):
        v = int((gy - y0) * z)
        cv2.line(big, (0, v), (bw, v), (0, 0, 255), 1)
        if gy % 24 == 0:
            cv2.putText(big, str(gy), (2, v + 9), cv2.FONT_HERSHEY_SIMPLEX, 0.32, (0, 0, 255), 1)
    # 画射线参考线：Q(235,458)->(795,443)
    cv2.line(big, (int((235 - x0) * z), int((458 - y0) * z)), (int((795 - x0) * z), int((443 - y0) * z)), (0, 0, 255), 2)
    out = os.path.join(SCRATCH, f"ray_{name}.png")
    cv2.imencode(".png", big)[1].tofile(out)
    print(name, (x0, y0, x1, y1))
