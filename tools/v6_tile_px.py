# -*- coding: utf-8 -*-
"""v6_tile_px.py — 帧级 tile_px 估算（纯离线，双判据局部窗交叉校验）。

给一张帧（BGR 或灰度），输出估算 tile_px 与所用判据：
 ① edge_step（城墙/墙体沿 x 的步长）：局部窗内强边缘列聚簇中心间距中位数，
    跨窗取中位；对应"连续城墙段周期性亮/暗跳变"。
 ② fft_texture（草地/墙面纹理网格周期）：局部窗 2D-FFT 径向主频，
    跨窗取中位；对应"草地纹理 FFT 找网格周期"。
 ③ blob_spacing（可选）：同排紧邻亮块（建筑）中心距中位数，失败 None。

一致性：①② 估值相对差 >15% → consensus=False 并报警；
估算取可用判据中位数，绝不只返回单一判据。仅依赖 cv2/numpy。
"""
import cv2
import numpy as np

SEARCH_LO, SEARCH_HI = 10, 90      # tile_px 搜索区间（px）
REL_TOL = 0.15                     # 两判据允许相对差
WIN, STRIDE = 120, 60              # 局部窗边长/步长


def _gray(frame):
    if frame.ndim == 3:
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return frame


def _windows(h, w, win=WIN, stride=STRIDE):
    for y in range(0, h - win + 1, stride):
        for x in range(0, w - win + 1, stride):
            yield x, y


def _edge_col_gap(we, lo=SEARCH_LO, hi=SEARCH_HI, frac=0.55):
    """窗内强边缘列聚簇中心间距中位数；样本不足 None。"""
    col = we.mean(axis=0)
    th = frac * float(col.max())
    idx = np.where(col > th)[0]
    if len(idx) < 4:
        return None
    clusters, cur = [], [float(idx[0])]
    for v in idx[1:]:
        if v - cur[-1] <= 3:
            cur.append(float(v))
        else:
            clusters.append(sum(cur) / len(cur))
            cur = [float(v)]
    clusters.append(sum(cur) / len(cur))
    gaps = np.diff(clusters)
    gaps = gaps[(gaps >= lo) & (gaps <= hi)]
    return float(np.median(gaps)) if len(gaps) >= 2 else None


def _fft_window_period(w, lo=SEARCH_LO, hi=SEARCH_HI):
    """单窗 2D-FFT 径向主频 → 周期(px)；无有效峰 None。"""
    h, ww = w.shape
    win = np.outer(np.hanning(h), np.hanning(ww))
    F = np.fft.fftshift(np.abs(np.fft.fft2(w * win)))
    cy, cx = h // 2, ww // 2
    F[cy - 3:cy + 4, cx - 3:cx + 4] = 0
    yy, xx = np.mgrid[0:h, 0:ww]
    r = np.hypot(yy - cy, xx - cx)
    rb = np.round(r).astype(int)
    maxr = min(h, ww) // 2 - 2
    prof = np.zeros(maxr)
    cnt = np.zeros(maxr)
    np.add.at(prof, rb[rb < maxr], F[rb < maxr])
    np.add.at(cnt, rb[rb < maxr], 1)
    prof = np.divide(prof, cnt, out=np.zeros_like(prof), where=cnt > 0)
    b_lo = max(4, int(ww / hi))
    b_hi = min(maxr - 1, int(ww / lo))
    seg = prof[b_lo:b_hi + 1]
    i = int(np.argmax(seg))
    return float(ww / (b_lo + i)) if seg[i] > 0 else None


def criterion_edge_step(frame):
    """① 局部窗聚合：强边缘列间距中位 → 墙体/网格沿 x 步长。返回 (值, 有效窗数)。"""
    g = _gray(frame)
    gx = cv2.Sobel(g, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(g, cv2.CV_64F, 0, 1, ksize=3)
    edge = np.hypot(gx, gy)
    vals = []
    for x, y in _windows(*edge.shape[:2]):
        v = _edge_col_gap(edge[y:y + WIN, x:x + WIN])
        if v is not None:
            vals.append(v)
    if not vals:
        return None, 0
    return float(np.median(vals)), len(vals)


def criterion_fft_texture(frame):
    """② 局部窗聚合：2D-FFT 径向周期中位 → 纹理网格周期。返回 (值, 有效窗数)。"""
    g = _gray(frame).astype(np.float64)
    vals = []
    for x, y in _windows(*g.shape[:2]):
        v = _fft_window_period(g[y:y + WIN, x:x + WIN])
        if v is not None:
            vals.append(v)
    if not vals:
        return None, 0
    return float(np.median(vals)), len(vals)


def criterion_blob_spacing(frame):
    """③（可选）亮块中心距中位数：阈值取建筑亮部，最近邻间距。失败 None。"""
    g = _gray(frame)
    _, th = cv2.threshold(g, 190, 255, cv2.THRESH_BINARY)
    cnts, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cents = []
    for c in cnts:
        area = cv2.contourArea(c)
        if 20 <= area <= 900:
            M = cv2.moments(c)
            if M["m00"] > 0:
                cents.append((M["m10"] / M["m00"], M["m01"] / M["m00"]))
    if len(cents) < 4:
        return None
    cents = np.float32(cents)
    nn = []
    for i, p in enumerate(cents):
        d = np.linalg.norm(cents - p, axis=1)
        d[i] = np.inf
        k = min(6, len(d) - 1)
        near = d[d < np.sort(d)[k]]
        if near.size:
            nn.append(float(np.min(near)))
    return float(np.median(nn)) if len(nn) >= 4 else None


def measure_tile_px(frame):
    """返回 dict：
    {estimate, consensus, rel_diff, warning, n_valid,
     criteria: {edge_step, fft_texture, blob_spacing}, used: [...]}
    """
    c1, n1 = criterion_edge_step(frame)
    c2, n2 = criterion_fft_texture(frame)
    c3 = criterion_blob_spacing(frame)
    vals = {"edge_step": c1, "fft_texture": c2, "blob_spacing": c3}
    used = {k: v for k, v in vals.items() if v is not None}
    core = [v for k, v in used.items() if k in ("edge_step", "fft_texture")]

    consensus, rel_diff, warning = True, None, []
    if len(core) >= 2:
        a, b = core
        rel_diff = abs(a - b) / max(a, b)
        if rel_diff > REL_TOL:
            consensus = False
            warning.append(f"判据①②相对差 {rel_diff:.1%} > {REL_TOL:.0%}，估值不可信")
    elif len(core) == 1:
        consensus = False
        warning.append("判据①②仅一项可用，缺交叉校验")
    else:
        consensus = False
        warning.append("判据①②均失败")

    if c3 is not None and len(core) == 2:
        rel3 = abs(c3 - np.median(core)) / max(c3, np.median(core))
        if rel3 > REL_TOL:
            warning.append(f"判据③与中位数差 {rel3:.1%}（仅参考，不否决）")

    estimate = float(np.median(list(used.values()))) if used else None
    return {
        "estimate": estimate,
        "consensus": consensus,
        "rel_diff": None if rel_diff is None else round(rel_diff, 4),
        "warning": "; ".join(warning),
        "n_valid": {"edge_step": n1, "fft_texture": n2},
        "criteria": {k: (None if v is None else round(v, 2)) for k, v in vals.items()},
        "used": list(used.keys()),
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        data = np.fromfile(sys.argv[1], dtype=np.uint8)
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        print(measure_tile_px(img))
    else:
        print("usage: python v6_tile_px.py <frame.png>")
