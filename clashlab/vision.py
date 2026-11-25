# -*- coding: utf-8 -*-
"""画面理解 v0.1：只做几何层——地图菱形与红色禁区边界，外加界面状态判定。

不做建筑分类。建筑检测需要训练模型，属于下一阶段；这里把“能算的东西”
先算出来，保证坐标、边界、HUD 这条链路可用。
"""
import logging
import os

import numpy as np
import cv2

from .geo import Calib, order_diamond

logger = logging.getLogger(__name__)

# P1-01：退化四边形最小面积（px²），小于即放弃标定，不进单应求解
MIN_QUAD_AREA = 400.0


def _quad_degenerate(quad):
    """前置校验：点数不足(<4) / 共线 / 面积过小 → (True, 原因)；否则 (False, "")。"""
    try:
        pts = np.asarray(quad, dtype=np.float64).reshape(-1, 2)
    except (ValueError, TypeError):
        return True, "坐标无法解析"
    if len(pts) < 4:
        return True, f"点数不足（{len(pts)} < 4）"
    # 共线判定：取任意三点围成的最大三角形面积 ≈ 0
    area = float(cv2.contourArea(pts.astype(np.float32)))
    if area < MIN_QUAD_AREA:
        return True, f"四边形面积过小（{area:.1f} < {MIN_QUAD_AREA}）"
    # 三点共线抽查：0-1-2 与 0-2-3 叉积
    for a, b, c in ((0, 1, 2), (0, 2, 3)):
        v1 = pts[b] - pts[a]
        v2 = pts[c] - pts[a]
        cross = abs(v1[0] * v2[1] - v1[1] * v2[0])
        if cross < 1e-3:
            return True, "三点共线"
    return False, ""


def safe_calib(quad, grid_n=44):
    """退化输入直接返回 None 并记日志，不进入单应求解（P1-01）。

    替代裸调 Calib.from_quad：点数不足/共线/面积过小/H 奇异都会在这里被拦，
    避免 geo.py:55 np.linalg.inv 抛 LinAlgError(Singular matrix) 崩抓帧流程。
    """
    deg, why = _quad_degenerate(quad)
    if deg:
        logger.warning("safe_calib: 边界退化（%s），放弃标定", why)
        return None
    try:
        calib = Calib.from_quad(quad, n=grid_n)
        np.linalg.inv(calib.H)  # 显式验证可逆，奇异则落入 except
        return calib
    except (np.linalg.LinAlgError, ValueError, cv2.error) as e:
        logger.warning("safe_calib: 单应退化 %s", e)
        return None


def imread(path):
    """读图，绕开中文路径：cv2.imread 在非 ASCII 路径下会失败。"""
    data = np.fromfile(path, dtype=np.uint8)
    if data.size == 0:
        return None
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def imwrite(path, img):
    ext = os.path.splitext(path)[1] or ".png"
    ok, buf = cv2.imencode(ext, img)
    if ok:
        buf.tofile(path)
    return ok


def platform_mask(frame):
    """石质地基：低饱和、偏亮的灰蓝铺装面。夜战主题下亮度会整体压低。"""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    s, v = cv2.split(hsv)[1], cv2.split(hsv)[2]
    m = ((v > 112) & (s < 108)).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((23, 23), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((11, 11), np.uint8))
    return m


def _largest_contour(mask, min_area_ratio=0.02, frame_area=None):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, 0.0
    best = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(best)
    if frame_area and area < frame_area * min_area_ratio:
        return None, 0.0
    return best, area


def red_mask(frame):
    b, g, r = cv2.split(frame)
    b = b.astype(np.int16)
    g = g.astype(np.int16)
    r = r.astype(np.int16)
    m = (r > 95) & ((r - g) > 28) & ((r - b) > 22) & (g < 165)
    m = (m.astype(np.uint8)) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    return m


def terrain_mask(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    m = ((h > 22) & (h < 95) & (s > 35) & (v > 45)).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
    return m


def _diamond_from_contour(c, frame_shape, eps_ratio=0.03):
    """把轮廓压成四点菱形；不达标返回 None。"""
    area = cv2.contourArea(c)
    hull = cv2.convexHull(c)
    peri = cv2.arcLength(hull, True)
    approx = cv2.approxPolyDP(hull, eps_ratio * peri, True).reshape(-1, 2)
    if len(approx) < 4:
        return None, area
    if len(approx) > 4:
        # 取与四个极值方向最远的点，凑成四点
        center = approx.mean(axis=0)
        dirs = np.array([[0, -1], [1, 0], [0, 1], [-1, 0]], dtype=np.float32)
        picked = []
        for d in dirs:
            proj = (approx - center) @ d
            picked.append(approx[int(np.argmax(proj))])
        approx = np.array(picked, dtype=np.float32)
    quad = order_diamond(approx)
    # 菱形质量：对角线比例应接近 2:1（等距投影）
    d1 = np.linalg.norm(quad[0] - quad[2])
    d2 = np.linalg.norm(quad[1] - quad[3])
    if d1 < 1 or d2 < 1:
        return None, area
    ratio = max(d1, d2) / min(d1, d2)
    if ratio > 2.9:
        return None, area
    return quad.astype(np.float32), area


def detect_boundary(frame, grid_n=44):
    """返回 (calib, meta)。优先用地图菱形，退而用红色禁区外扩。"""
    fh, fw = frame.shape[:2]
    frame_area = fh * fw
    meta = {"source": None, "area_ratio": 0.0, "ratio": 0.0, "confidence": 0.0}

    cand = None
    for name, mask, expand in (("platform", platform_mask(frame), 1.0),
                               ("terrain", terrain_mask(frame), 1.0),
                               ("redzone", red_mask(frame), 1.08)):
        c, area = _largest_contour(mask, 0.06, frame_area)
        if c is None:
            continue
        quad, area2 = _diamond_from_contour(c, frame.shape)
        if quad is None:
            continue
        d1 = np.linalg.norm(quad[0] - quad[2])
        d2 = np.linalg.norm(quad[1] - quad[3])
        ratio = min(d1, d2) / max(d1, d2)
        area_ratio = cv2.contourArea(quad) / frame_area
        # 地基是主要线索：面积越大越可信；地形与红区小幅加权
        weight = {"platform": 1.0, "terrain": 0.55, "redzone": 0.8}[name]
        score = weight * ratio * min(area_ratio * 2.2, 1.0)
        # P2-3 实机发现：基地放大到充满屏幕时，平台轮廓被画面边界裁掉，四角贴边但面积比很高，
        # 置信虚高（实测 0.975）。此处对「贴边四边形」降权，交由 boundary_assessment 判不可用。
        margin = 2.5
        clipped = any(x <= margin or x >= fw - 1 - margin or y <= margin or y >= fh - 1 - margin
                      for x, y in quad)
        if clipped:
            score *= 0.35
        if expand != 1.0 and area_ratio < 0.55:
            ctr = quad.mean(axis=0)
            quad = ctr + (quad - ctr) * expand
        if cand is None or score > cand[0]:
            cand = (score, quad, name, area_ratio, ratio, clipped)

    if cand is None:
        return None, meta

    score, quad, name, area_ratio, ratio, clipped = cand
    calib = safe_calib(quad, grid_n=grid_n)  # P1-01：退化/奇异返回 None，不抛 LinAlgError
    if calib is None:
        return None, meta
    meta.update({"source": name, "area_ratio": float(area_ratio),
                 "ratio": float(ratio), "confidence": float(score),
                 "clipped": bool(clipped),
                 "quad": [[float(x), float(y)] for x, y in quad]})
    return calib, meta


def boundary_assessment(calib, meta, min_conf=0.05):
    """P2 可用性判定：由 detect_boundary 的 meta 推导 usable / usable_reason / labels_source。

    只读已有字段、不改标定结果；返回可并入 meta/extra 的字典：
    usable(bool)、usable_reason、labels_source、confidence、quad_available、source。
    "不可用"是合法结论，不在这里伪造标定。
    """
    meta = meta or {}
    conf = float(meta.get("confidence", 0.0) or 0.0)
    out = {"usable": False, "usable_reason": "", "labels_source": "unavailable",
           "confidence": round(conf, 4), "quad_available": calib is not None,
           "source": meta.get("source")}
    if calib is None:
        out["usable_reason"] = "detect_boundary 未给出 calib：未找到合格地图菱形"
        out["labels_source"] = "no_calib"
        return out
    if meta.get("clipped"):
        out["usable_reason"] = "菱形贴边（画面被裁切），面积与四角不可信，不能用于网格换算"
        out["labels_source"] = "clipped"
        return out
    if conf < min_conf:
        out["usable_reason"] = f"边界置信度过低（{conf:.3f} < {min_conf}），不可用于网格换算"
        out["labels_source"] = "low_confidence"
        return out
    out["usable"] = True
    out["usable_reason"] = f"边界可用（source={meta.get('source')}, conf={conf:.3f}）"
    return out


def detect_dialog(frame):
    """识别“还在吗/连接断开”这类弹窗：压暗背景 + 中央纯灰面板（实测 RGB 66,66,66）。"""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    s, v = cv2.split(hsv)[1], cv2.split(hsv)[2]
    m = ((s < 26) & (v > 48) & (v < 100)).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((17, 17), np.uint8))
    c, area = _largest_contour(m, 0.10, frame.shape[0] * frame.shape[1])
    if c is None:
        return {"present": False}
    x, y, w, h = cv2.boundingRect(c)
    rect_fill = area / max(w * h, 1)
    if rect_fill < 0.55 or w < frame.shape[1] * 0.3 or h < frame.shape[0] * 0.12:
        return {"present": False}
    return {"present": True, "box": [int(x), int(y), int(w), int(h)],
            "coverage": round(area / (frame.shape[0] * frame.shape[1]), 3),
            "reload_btn": [round(x + w * 0.10), round(y + h * 0.80)]}


def screen_state(frame, focus="", boundary_meta=None):
    """粗糙但明确的界面判定，够用即可，后续换模板/分类器。"""
    if focus and "clashofclans" in focus.lower():
        base = "coc"
    else:
        base = "other"

    meta = boundary_meta or {}
    red_ratio = float(meta.get("red_area_ratio", 0.0))
    if base == "coc":
        if meta.get("source") == "redzone" and red_ratio > 0.35:
            return "deploy"
        if meta.get("source") in ("terrain", "redzone", "platform"):
            return "base"
        return "coc_unknown"
    return base


def deployable_mask(calib, n=44, inset=1):
    """可用撒兵区：菱形外环减去一点边距，近似部署区。"""
    m = np.zeros((n + 1, n + 1), np.uint8)
    m[inset:n + 1 - inset, inset:n + 1 - inset] = 1
    ring = m.copy()
    ring[inset + 3:n + 1 - inset - 3, inset + 3:n + 1 - inset - 3] = 0
    return ring


def quad_polygon(calib, frame_shape):
    quad = np.array(calib.quad, dtype=np.int32)
    mask = np.zeros(frame_shape[:2], np.uint8)
    cv2.fillPoly(mask, [quad], 255)
    return mask


def structure_mask(frame, inside):
    """地基之上的“非铺装”像素：密集饱和色、极亮或极暗的块，通常是建筑。"""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    s, v = cv2.split(hsv)[1], cv2.split(hsv)[2]
    m = ((s > 72) | (v > 188) | (v < 46)).astype(np.uint8) * 255
    m = cv2.bitwise_and(m, inside)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    return m


def structure_mask_v2(frame, inside):
    """真实夜间/洞穴帧适配版结构 mask（新增，不改旧 structure_mask）。

    旧版 (s>72)|(v>188)|(v<46) 在洞穴蓝地面上失效：蓝地 H≈100-130、s 中位≈90，
    被 s>72 整片吞成前景，连通域合并成巨块后被面积上限过滤 → 0 候选。
    v2 只取暖色建筑（H<18 或 H>165 且 s>55）与高亮块（v>200），主动排除蓝地面。
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    warm = (s > 55) & ((h < 18) | (h > 165))
    bright = v > 200
    m = ((warm | bright) & (inside > 0)).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((11, 11), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    return m


def detect_structures_v2(frame, calib, mask=None):
    """与 detect_structures 同 schema 的候选检测（新增函数，旧函数不动）。

    mask 缺省用 structure_mask_v2；tile 落在标定区外的候选丢弃（quad 偏位时降噪）。
    返回项额外带 source_mask 字段，供报告区分新旧检测器。
    """
    if calib is None:
        return []
    inside = quad_polygon(calib, frame.shape)
    m = mask if mask is not None else structure_mask_v2(frame, inside)
    quad_area = float((inside > 0).sum())
    n, _labels, stats, _cents = cv2.connectedComponentsWithStats(m, connectivity=8)
    out = []
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if area < quad_area * 0.0016 or area > quad_area * 0.09:
            continue
        if w < 8 or h < 8 or w / max(h, 1) > 3.2:
            continue
        foot = (x + w / 2.0, y + h * 0.78)
        try:
            gx, gy = calib.px_to_tile(foot[0], foot[1])
        except np.linalg.LinAlgError as e:  # P1-01：H 奇异兜底，跳过该候选不崩整帧
            logger.warning("detect_structures_v2: px_to_tile 奇异矩阵，跳过候选 %s", e)
            continue
        if not (0 <= gx <= 44 and 0 <= gy <= 44):
            continue  # quad 偏位时，落在标定区外的暖色块不进候选
        tw, _ = calib.tile_to_px(1, 0)
        tile_px = max(abs(tw - calib.tile_to_px(0, 0)[0]), 1.0)
        size_k = int(np.clip(round((w / tile_px) / 1.4), 2, 4))
        out.append({"type": None, "box": (int(x), int(y), int(w), int(h)), "area": int(area),
                    "tile": (round(float(gx), 1), round(float(gy), 1)),
                    "size": size_k, "score": 0.0, "source_mask": "v2_warm"})
    out.sort(key=lambda d: -d["area"])
    return out


def detect_structures(frame, calib):
    """地块级建筑检测：连通域 → 瓦片坐标 → 占地格数。定位靠几何，类型靠模板补充。"""
    if calib is None:
        return []
    inside = quad_polygon(calib, frame.shape)
    m = structure_mask(frame, inside)
    quad_area = float((inside > 0).sum())
    n, labels, stats, cents = cv2.connectedComponentsWithStats(m, connectivity=8)
    out = []
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if area < quad_area * 0.0016 or area > quad_area * 0.09:
            continue
        if w < 8 or h < 8 or w / max(h, 1) > 3.2:
            continue
        # 等距投影下建筑“脚”在包围盒偏下位置
        foot = (x + w / 2.0, y + h * 0.78)
        try:
            gx, gy = calib.px_to_tile(foot[0], foot[1])
        except np.linalg.LinAlgError as e:  # P1-01：H 奇异兜底，跳过该候选不崩整帧
            logger.warning("detect_structures: px_to_tile 奇异矩阵，跳过候选 %s", e)
            continue
        tw, _ = calib.tile_to_px(1, 0)
        tile_px = max(abs(tw - calib.tile_to_px(0, 0)[0]), 1.0)
        size_k = int(np.clip(round((w / tile_px) / 1.4), 2, 4))
        out.append({"type": None, "box": (int(x), int(y), int(w), int(h)), "area": int(area),
                    "tile": (round(float(gx), 1), round(float(gy), 1)),
                    "size": size_k, "score": 0.0})
    out.sort(key=lambda d: -d["area"])
    return out


def assign_types(dets, matches, max_dist_tile=1.6):
    """把模板命中的类型贴到最近的地块上。"""
    if not matches:
        return dets
    for m in matches:
        bx, by, bw, bh = m["box"]
        cx, cy = bx + bw / 2.0, by + bh * 0.72
        best, bd = None, 1e9
        for d in dets:
            dx, dy, dw, dh = d["box"]
            kx, ky = dx + dw / 2.0, dy + dh * 0.78
            dist = ((cx - kx) ** 2 + (cy - ky) ** 2) ** 0.5 / max(dw, dh)
            if dist < bd:
                best, bd = d, dist
        if best is not None and bd < max_dist_tile and m["score"] >= best["score"]:
            best["type"] = m["type"]
            best["score"] = round(m["score"], 3)
            best["tpl_box"] = m["box"]
    return dets


def buildings_to_sim(dets, n=44):
    """检测结果 → 模拟器建筑清单。未识别类型的按占地大小给近似防御数值。"""
    from . import assets
    from .sim import Simulator
    sim = Simulator(n=n)
    generic = {2: (1200, 110), 3: (1600, 130), 4: (2600, 150)}
    for d in dets:
        st = assets.STATS.get(d["type"]) if d["type"] else None
        if st:
            hp, dps, rng = st["hp"], st["dps"], st["range"]
            size = st["size"]
        else:
            hp, dps = generic.get(d["size"], (1400, 120))
            rng, size = 9, d["size"]
        tile = (int(np.clip(round(d["tile"][0]), 0, n)), int(np.clip(round(d["tile"][1]), 0, n)))
        sim.add_building(d["type"] or "defense", tile, hp, dps, rng)
        d["stat"] = {"hp": hp, "dps": dps, "size": size}
    return sim


def analyze_frame(frame, focus=""):
    """一次完整解析：边界标定 + 界面状态（含挂机/断线弹窗）。"""
    calib, meta = detect_boundary(frame)

    rm = red_mask(frame)
    red_area = float((rm > 0).sum()) / float(frame.shape[0] * frame.shape[1])
    meta["red_area_ratio"] = red_area

    dialog = detect_dialog(frame)
    base_state = screen_state(frame, focus, meta)
    state = "dialog" if (dialog.get("present") and "clashofclans" in (focus or "").lower()) else base_state

    out = {
        "size": [int(frame.shape[1]), int(frame.shape[0])],
        "state": state,
        "base_state": base_state,
        "focus": focus,
        "dialog": dialog,
        "boundary": meta,
        "red_ratio": round(red_area, 3),
        "calib": calib.to_dict() if calib else None,
        "reproj": round(calib.reproj_error(), 2) if calib else None,
    }
    return out, calib


def scan_layout(frame, calib, use_templates=True, thresh=0.5):
    """识别建筑：连通域打底 + 模板补类型。返回 (detections, matches, meta)。"""
    from . import assets
    dets = detect_structures(frame, calib)
    meta = {"structures": len(dets), "matched": 0, "tile_px": None}
    matches = []
    if calib is not None:
        try:
            a = calib.tile_to_px(0, 0)
            b = calib.tile_to_px(1, 0)
            tile_px = abs(b[0] - a[0]) + abs(b[1] - a[1])
            meta["tile_px"] = round(float(tile_px), 2)
            if use_templates and dets:
                matches = assets.match_buildings(frame, tile_px, thresh=thresh)
                dets = assign_types(dets, matches)
                meta["matched"] = sum(1 for d in dets if d["type"])
        except Exception as e:
            meta["error"] = str(e)
    return dets, matches, meta
