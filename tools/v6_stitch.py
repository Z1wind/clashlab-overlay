# -*- coding: utf-8 -*-
"""v6_stitch.py — 分块拼接工具（纯离线，只读调用，不改任何现有模块）。

用途：执行线把"最大放大档"分块截图按序喂入，本工具拼回整幅并做缝校验。

能力：
- 输入：有序分块 list[np.ndarray] + 可选实测位移 offsets=[(dx,dy), ...]；
  不给位移时按"网格 + 重叠比"先验，再用相位相关在重叠条带内精修。
- 缝校验：邻接块重叠条带相位相关残差（sub-px）；ORB 特征匹配复核；
  错位 > max_seam_px(默认4px) 判不合格，该块标记 need_rescan。
- 输出：拼接大图 + stitch_report.json（每块 dx/dy、重叠尺寸、缝错位、合格与否）。

约定：分块按行优先顺序；网格行列数可传 grid=(rows,cols)，不传按 1 行展开推断。
仅依赖 cv2/numpy；不读屏、不联网、不动 adb。
"""
import json
import os
import cv2
import numpy as np

MAX_SEAM_PX = 4.0
ORB_NFEATURES = 500


def _gray(a):
    if a.ndim == 3:
        return cv2.cvtColor(a, cv2.COLOR_BGR2GRAY)
    return a


def phase_shift(a, b):
    """a 与 b（同尺寸重叠条带）相位相关，返回 (dx, dy, response)：
    b 相对 a 的亚像素位移；response 越大峰越锐。"""
    ga, gb = _gray(a).astype(np.float64), _gray(b).astype(np.float64)
    h, w = ga.shape[:2]
    win = cv2.createHanningWindow((w, h), cv2.CV_64F)
    (dx, dy), resp = cv2.phaseCorrelate(ga, gb, win)
    return float(dx), float(dy), float(resp)


def orb_residual(a, b, max_matches=80):
    """ORB 特征匹配复核重叠区几何一致性。返回 (中位偏移px, 内点数)；失败返回 (None, 0)。"""
    ga, gb = _gray(a), _gray(b)
    orb = cv2.ORB_create(ORB_NFEATURES)
    ka, da = orb.detectAndCompute(ga, None)
    kb, db = orb.detectAndCompute(gb, None)
    if da is None or db is None or len(ka) < 8 or len(kb) < 8:
        return None, 0
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    knn = bf.knnMatch(da, db, k=2)
    good = [m for m, n in knn if m.distance < 0.75 * n.distance]
    if len(good) < 6:
        return None, len(good)
    pa = np.float32([ka[m.queryIdx].pt for m in good])
    pb = np.float32([kb[m.trainIdx].pt for m in good])
    d = np.linalg.norm(pb - pa, axis=1)
    return float(np.median(d)), len(good)


def _expected_positions(n, tile_w, tile_h, overlap, grid):
    """先验位置：stride = 块长×(1-overlap)。"""
    if grid is None:
        grid = (1, n)
    rows, cols = grid
    pos = []
    for r in range(rows):
        for c in range(cols):
            pos.append((c * tile_w * (1 - overlap), r * tile_h * (1 - overlap)))
    return pos


def stitch(tiles, offsets=None, overlap=0.2, grid=None, max_seam_px=MAX_SEAM_PX,
           report_path=None):
    """拼接。

    tiles: 行优先分块；offsets: [(dx,dy)] 绝对位置（None=自动）；
    overlap: 重叠比（常规 0.20）；grid=(rows,cols)；max_seam_px: 缝阈值。
    返回 (canvas, report)。canvas 为 BGR；report 同时落盘到 report_path（若给）。
    """
    tiles = [np.asarray(t) for t in tiles]
    n = len(tiles)
    th, tw = tiles[0].shape[:2]
    if grid is None:
        grid = (1, n)
    rows, cols = grid
    if offsets is None:
        priors = _expected_positions(n, tw, th, overlap, grid)
    else:
        priors = [tuple(float(v) for v in o) for o in offsets]

    placed = []          # (x, y)
    report = {"overlap": overlap, "max_seam_px": max_seam_px,
              "tile_size": [tw, th], "grid": [rows, cols],
              "tiles": [], "all_pass": True}
    ov_w = int(round(tw * overlap))
    ov_h = int(round(th * overlap))

    for i, t in enumerate(tiles):
        c, r = i % cols, i // cols
        px, py = priors[i]
        seam = {"index": i, "dx": px, "dy": py,
                "overlap_w": ov_w, "overlap_h": ov_h,
                "seam_err_px": None, "seam_dx": None, "seam_dy": None,
                "orb_med_px": None, "orb_inliers": 0,
                "overlap_mad": None, "pass": True, "need_rescan": False,
                "refined": False}
        auto = offsets is None
        # —— 自动模式：相位相关精修先验位移（给了实测位移则不挪动）——
        rx = ry = 0.0
        if auto and c > 0:
            la, lb = tiles[i - 1][:, -ov_w:], t[:, :ov_w]
            dx, dy, _ = phase_shift(la, lb)
            rx += dx
            seam["refined"] = True
        if auto and r > 0:
            ua, ub = tiles[i - cols][-ov_h:, :], t[:ov_h, :]
            _, dy2, _ = phase_shift(ua, ub)
            ry += dy2
            seam["refined"] = True
        fx = px + (rx if c > 0 else 0.0)
        fy = py + (ry if r > 0 else 0.0)
        seam["dx"], seam["dy"] = fx, fy

        # —— 缝错位：最终放置后，与左/上邻在画布重叠矩形内相位相关残差 ——
        res = []
        ov_crops = []
        if c > 0:
            nx0 = placed[i - 1][0]
            ox0 = max(nx0, fx)
            ox1 = min(nx0 + tw, fx + tw)
            if ox1 - ox0 >= 8:
                a0 = int(round(ox0 - nx0)); a1 = int(round(ox1 - nx0))
                b0 = int(round(ox0 - fx)); b1 = int(round(ox1 - fx))
                ww = min(a1 - a0, b1 - b0)
                A = tiles[i - 1][:, a0:a0 + ww]
                B = t[:, b0:b0 + ww]
                dx, dy, _ = phase_shift(A, B)
                res.append((dx, dy))
                ov_crops.append((A, B))
        if r > 0:
            ny0 = placed[i - cols][1]
            oy0 = max(ny0, fy)
            oy1 = min(ny0 + th, fy + th)
            if oy1 - oy0 >= 8:
                a0 = int(round(oy0 - ny0)); a1 = int(round(oy1 - ny0))
                b0 = int(round(oy0 - fy)); b1 = int(round(oy1 - fy))
                hh = min(a1 - a0, b1 - b0)
                A = tiles[i - cols][a0:a0 + hh, :]
                B = t[b0:b0 + hh, :]
                dx, dy, _ = phase_shift(A, B)
                res.append((dx, dy))
                ov_crops.append((A, B))
        if res:
            dxm = max(abs(a) for a, _ in res)
            dym = max(abs(b) for _, b in res)
            seam_err = float(np.hypot(dxm, dym))
            seam["seam_dx"], seam["seam_dy"] = round(dxm, 3), round(dym, 3)
            seam["seam_err_px"] = round(seam_err, 3)
            seam["pass"] = seam_err <= max_seam_px
            seam["need_rescan"] = not seam["pass"]

        # —— ORB 复核 + 重叠区 MAD（取公共重叠 crop）——
        if ov_crops:
            A, B = ov_crops[0]
            med, nin = orb_residual(A, B)
            seam["orb_med_px"] = None if med is None else round(med, 2)
            seam["orb_inliers"] = nin
            seam["overlap_mad"] = round(float(np.mean(
                np.abs(_gray(A).astype(np.int16) - _gray(B).astype(np.int16)))), 2)

        placed.append((fx, fy))
        report["tiles"].append(seam)
        if not seam["pass"]:
            report["all_pass"] = False

    # —— 画布与粘贴（后块覆盖；精确恢复时重叠像素一致）——
    rnd = [(int(round(x)), int(round(y))) for x, y in placed]
    max_x = max(x + tw for x, _ in rnd)
    max_y = max(y + th for _, y in rnd)
    canvas = np.zeros((int(max_y), int(max_x), 3), np.uint8)
    for i, t in enumerate(tiles):
        x, y = rnd[i]
        h, w = t.shape[:2]
        canvas[y:y + h, x:x + w] = t

    if report_path:
        os.makedirs(os.path.dirname(os.path.abspath(report_path)), exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    return canvas, report


if __name__ == "__main__":
    # 轻量自检入口见 tools/v6_selftest.py；本文件库用法：
    # from v6_stitch import stitch
    print("v6_stitch library; use stitch(tiles, offsets=None, overlap=0.2, grid=(r,c))")
