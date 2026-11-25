# -*- coding: utf-8 -*-
# l0v2_align.py — A(two-shot) 与 B(three-shot) ORB 配准，输出单应与对齐叠图（纯离线）
import os, cv2, numpy as np, json
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OV = os.path.join(ROOT, "out", "overlay")
OUT = os.path.join(ROOT, "tools", "base_out")
A = cv2.imdecode(np.fromfile(os.path.join(OV, "v6_l0_two_shot_base.png"), dtype=np.uint8), cv2.IMREAD_COLOR)
B = cv2.imdecode(np.fromfile(os.path.join(OV, "v6_l0_three_shot_base.png"), dtype=np.uint8), cv2.IMREAD_COLOR)
ga, gb = cv2.cvtColor(A, cv2.COLOR_BGR2GRAY), cv2.cvtColor(B, cv2.COLOR_BGR2GRAY)
orb = cv2.ORB_create(1500)
ka, da = orb.detectAndCompute(ga, None)
kb, db = orb.detectAndCompute(gb, None)
bf = cv2.BFMatcher(cv2.NORM_HAMMING)
knn = bf.knnMatch(da, db, k=2)
good = [m for m, n in knn if m.distance < 0.75 * n.distance]
print("good matches", len(good))
pa = np.float32([ka[m.queryIdx].pt for m in good])
pb = np.float32([kb[m.trainIdx].pt for m in good])
H, mask = cv2.findHomography(pa, pb, cv2.RANSAC, 4.0)
inl = int(mask.sum())
print("homography inliers", inl, "/", len(good))
print("H=", np.round(H, 3).tolist())
# 把 A  warp 到 B 画布，红绿叠图
hB, wB = B.shape[:2]
warpA = cv2.warpPerspective(A, H, (wB, hB))
blend = cv2.addWeighted(B, 0.55, warpA, 0.45, 0)
cv2.imencode(".png", blend)[1].tofile(os.path.join(OUT, "align_blend.png"))
# 对应点连线图
draw = cv2.drawMatches(A, ka, B, kb, good, None, matchesMask=mask.ravel().tolist(), flags=2)
cv2.imencode(".png", draw)[1].tofile(os.path.join(OUT, "align_matches.png"))
json.dump({"H": H.round(4).tolist(), "good": len(good), "inliers": inl},
          open(os.path.join(OUT, "align_H.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
