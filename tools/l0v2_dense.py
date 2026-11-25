# -*- coding: utf-8 -*-
# l0v2_dense.py — 对齐后密网格 A->B 匹配，输出高NCC点标注图与清单（纯离线）
import os, cv2, numpy as np, json
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OV = os.path.join(ROOT, "out", "overlay")
OUT = os.path.join(ROOT, "tools", "base_out", "v2")
A = cv2.imdecode(np.fromfile(os.path.join(OV, "v6_l0_two_shot_base.png"), dtype=np.uint8), cv2.IMREAD_COLOR)
B = cv2.imdecode(np.fromfile(os.path.join(OV, "v6_l0_three_shot_base.png"), dtype=np.uint8), cv2.IMREAD_COLOR)
H = np.array(json.load(open(os.path.join(OUT, "..", "align_H.json"), encoding="utf-8"))["H"])
ga, gb = cv2.cvtColor(A, cv2.COLOR_BGR2GRAY), cv2.cvtColor(B, cv2.COLOR_BGR2GRAY)

# A 中网格窗口（64px，步长40），在 B 中以 H 映射点为中心 ±35px 搜索
WIN = 64; STEP = 40; R = 35
hA, wA = A.shape[:2]
hits = []
for y in range(40, hA - WIN - 40, STEP):
    for x in range(40, wA - WIN - 40, STEP):
        tpl = ga[y:y + WIN, x:x + WIN]
        # 期望 B 位置
        p = H @ np.array([x + WIN / 2, y + WIN / 2, 1.0])
        bx, by = int(p[0] / p[2]), int(p[1] / p[2])
        x0, y0 = max(0, bx - R), max(0, by - R)
        x1, y1 = min(gb.shape[1] - WIN + 1, bx + R), min(gb.shape[0] - WIN + 1, by + R)
        if x1 - x0 < WIN or y1 - y0 < WIN:
            continue
        roi = gb[y0:y1, x0:x1]
        res = cv2.matchTemplate(roi, tpl, cv2.TM_CCOEFF_NORMED)
        _, mx, _, ml = cv2.minMaxLoc(res)
        if mx >= 0.72:
            gx, gy = x0 + ml[0], y0 + ml[1]
            hits.append((x, y, gx, gy, round(float(mx), 3)))
print("hits>=0.72:", len(hits))
# NMS：B 坐标 50px 去重
hits.sort(key=lambda h: -h[4])
keep = []
for h in hits:
    if all((h[2] - k[2]) ** 2 + (h[3] - k[3]) ** 2 > 55 ** 2 for k in keep):
        keep.append(h)
print("nms keep:", len(keep))
vis = B.copy()
for x, y, gx, gy, s in keep:
    cv2.rectangle(vis, (gx, gy), (gx + WIN, gy + WIN), (0, 255, 0), 2)
    cv2.putText(vis, f"{s:.2f}", (gx, gy - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
cv2.imencode(".png", vis)[1].tofile(os.path.join(OUT, "dense_hits_B.png"))
json.dump(keep, open(os.path.join(OUT, "dense_hits.json"), "w", encoding="utf-8"))
for h in keep:
    print(h)
