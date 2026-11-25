# -*- coding: utf-8 -*-
"""本地素材库模板比对（snap 专用，不联网、不调大模型）。

发现顺序：
1. manifest_buildings.json（含 type/level/w_tiles/h_tiles/file）优先；
2. 无 manifest：目录 {type}/level-{n}.png，目录名经 ALIAS 归一；
3. 平铺 {type}_l{level}.png 兼容。

匹配方式（第二轮修正）：
- 期望尺寸 = w_tiles/h_tiles × tile_px（±20%），不再拿 128px 模板硬缩；
- alpha 掩膜 CCOEFF_NORMED 主分；BGR 均值相似度二次校验；
- 几何先验：候选框宽高比与模板 w/h_tiles 一致性强过滤；
- 纯全图 CCORR 只找位置，不当分类分。
"""
import glob
import json
import os
import re

import cv2
import numpy as np

_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "coc", "buildings")

ALIAS = {
    "air-defense": "airdef", "eagle-artillery": "eagle", "scattershot": "scatter",
    "inferno-tower": "inferno", "x-bow": "xbow", "wizard-tower": "wiztower",
    "cannon": "cannon", "archer-tower": "archertower", "mortar": "mortar",
    "air-sweeper": "sweeper", "town-hall": "townhall", "bomb-tower": "bombtower",
    "hidden-tesla": "tesla", "spell-tower": "spelltower",
    "multi-archer-tower": "multiarcher", "firespitter": "firespitter",
    "monolith": "monolith",
}

HOME_NAME = {
    "airdef": "air-defense", "eagle": "eagle-artillery", "scatter": "scattershot",
    "inferno": "inferno-tower", "xbow": "x-bow", "wiztower": "wizard-tower",
    "archertower": "archer-tower", "sweeper": "air-sweeper", "townhall": "town-hall",
    "bombtower": "bomb-tower", "tesla": "hidden-tesla", "spelltower": "spell-tower",
    "multiarcher": "multi-archer-tower",
}

EXPECTED_TYPES = sorted(set(ALIAS.values()))


def canon(type_alias):
    return HOME_NAME.get(type_alias, type_alias)


def _bgra(path):
    data = np.fromfile(path, dtype=np.uint8)
    if data.size == 0:
        return None
    return cv2.imdecode(data, cv2.IMREAD_UNCHANGED)


def discover_manifest(root):
    """读 manifest_buildings.json → {canon: [entry,...]}；无 manifest 返回 {}。"""
    manifest = os.path.join(root, "manifest_buildings.json")
    if not os.path.exists(manifest):
        return {}
    try:
        with open(manifest, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {}
    items = data.get("entries") or data.get("buildings") or data.get("items") or []
    out = {}
    for it in items:
        t = it.get("type")
        rel = it.get("file")
        if not t or not rel:
            continue
        rel = rel.replace("/", os.sep)
        # manifest 的 file 可能已含 assets/coc/buildings 前缀：依次试 root 拼接、原样、项目根拼接
        candidates = [os.path.join(root, rel), rel,
                      os.path.join(os.path.dirname(os.path.dirname(root)), rel)]
        resolved = next((p for p in candidates if os.path.exists(p)), None)
        out.setdefault(t, []).append({
            "file": resolved or os.path.join(root, rel),
            "level": it.get("level"),
            "w_tiles": float(it.get("w_tiles") or 2),
            "h_tiles": float(it.get("h_tiles") or 2),
            "px_w": it.get("px_w"), "px_h": it.get("px_h"),
        })
    return out


def discover_dirs(root):
    """manifest 缺失时的目录/平铺回退。"""
    out = {}
    if not root or not os.path.isdir(root):
        return out
    for name in sorted(os.listdir(root)):
        dp = os.path.join(root, name)
        if not os.path.isdir(dp) or name.startswith("_"):
            continue
        canonical = ALIAS.get(name, name)
        for p in sorted(glob.glob(os.path.join(dp, "level-*.png"))):
            out.setdefault(canonical, []).append({
                "file": p, "level": None, "w_tiles": 2.0, "h_tiles": 2.0,
                "px_w": None, "px_h": None,
            })
    for p in sorted(glob.glob(os.path.join(root, "*.png"))):
        m = re.match(r"(.+)_l(\d+)\.png$", os.path.basename(p))
        if m:
            out.setdefault(m.group(1), []).append({
                "file": p, "level": None, "w_tiles": 2.0, "h_tiles": 2.0,
                "px_w": None, "px_h": None,
            })
    return out


class TemplateBank:
    """manifest 优先加载；按期望尺寸掩膜匹配 + 几何/颜色校验 + 全局 NMS。"""

    def __init__(self, root=_ROOT, use_templates=True):
        self.use_templates = bool(use_templates)
        self.root = root or _ROOT
        self.manifest = discover_manifest(self.root) if self.use_templates else {}
        self.fallback = discover_dirs(self.root) if self.use_templates and not self.manifest else {}
        self._img_cache = {}

    @property
    def types(self):
        return sorted(set(self.manifest) | set(self.fallback))

    def missing_types(self):
        have = set(self.types)
        return [t for t in EXPECTED_TYPES if t not in have]

    def _entries(self, canonical):
        return self.manifest.get(canonical) or self.fallback.get(canonical) or []

    def _rep_entry(self, canonical):
        """每类型只取代表级（中位 level），避免 220 条全量扫描。"""
        entries = self._entries(canonical)
        if not entries:
            return None
        levels = [(e.get("level") or 0, e) for e in entries]
        levels.sort(key=lambda t: t[0])
        return levels[len(levels) // 2][1]

    def _img(self, entry):
        key = entry["file"]
        if key not in self._img_cache:
            try:
                self._img_cache[key] = _bgra(entry["file"])
            except (FileNotFoundError, OSError):
                self._img_cache[key] = None
        return self._img_cache[key]

    @staticmethod
    def _aspect_ok(box_wh, w_tiles, h_tiles, tol=0.38):
        bw, bh = box_wh
        exp = w_tiles / max(h_tiles, 0.2)
        got = bw / max(bh, 1.0)
        return abs(got - exp) / max(exp, 0.2) <= tol

    @staticmethod
    def _color_ok(bgr_crop, tpl_bgra, msk, tol=0.45):
        """掩膜内 BGR 均值余弦相似度 ≥1-tol。"""
        a = bgr_crop.reshape(-1, 3).astype(np.float32)
        tm = tpl_bgra[:, :, :3].reshape(-1, 3).astype(np.float32)
        m = msk.reshape(-1) > 0
        if m.sum() < 20:
            return True
        va = a[m].mean(axis=0)
        vt = tm[m].mean(axis=0)
        na, nt = np.linalg.norm(va), np.linalg.norm(vt)
        if na < 1 or nt < 1:
            return True
        cos = float(va @ vt / (na * nt))
        return cos >= (1 - tol)

    def scan(self, gray, bgr, tile_px, roi=None, min_score=0.60, nms_dist=1.1,
             only_types=None, scales=(0.85, 1.0, 1.18)):
        """ROI 内按期望尺寸扫描 → [{type,score,box,w_tiles,h_tiles}]。

        only_types: 只扫这些 canonical 类型（None=全部）；用于覆盖层"重要建筑"快扫。
        scales: 尺度枚举；少给几档可显著缩短耗时（每档一次全图 matchTemplate）。
        """
        if not self.use_templates or not self.types:
            return []
        types = self.types
        if only_types:
            want = {canon(t) for t in only_types}
            types = [t for t in types if canon(t) in want]
        if not types:
            return []
        fh, fw = gray.shape[:2]
        rx0, ry0, rx1, ry1 = roi or (int(fw * 0.14), int(fh * 0.14), int(fw * 0.88), int(fh * 0.86))
        region_g = gray[ry0:ry1, rx0:rx1]
        region_b = bgr[ry0:ry1, rx0:rx1]
        raw = []
        for canonical in types:
            entry = self._rep_entry(canonical)
            if entry is None:
                continue
            img = self._img(entry)
            if img is None or img.shape[2] != 4:
                continue
            exp_w = entry["w_tiles"] * tile_px
            exp_h = entry["h_tiles"] * tile_px
            for k in scales:
                tw, th = max(9, int(exp_w * k)), max(9, int(exp_h * k))
                if tw >= region_g.shape[1] or th >= region_g.shape[0] or tw < 10:
                    continue
                r = cv2.resize(img, (tw, th), interpolation=cv2.INTER_AREA)
                msk = (r[:, :, 3] > 40).astype(np.uint8) * 255
                tg = cv2.cvtColor(r, cv2.COLOR_BGRA2GRAY)
                res = cv2.matchTemplate(region_g, tg, cv2.TM_CCOEFF_NORMED, mask=msk)
                # 带 mask 的 TM_CCOEFF_NORMED 在平坦区域会给出 inf/nan：一律归 0，
                # 否则 nan_to_num 会把它变成 float32 最大值 3.4e38，假阳性压掉真命中。
                res = np.nan_to_num(res, nan=0.0, posinf=0.0, neginf=0.0)
                res = np.clip(res, -1.0, 1.0)
                ys, xs = np.where(res >= min_score)
                for y, x in zip(ys, xs):
                    geo_ok = self._aspect_ok((tw, th), entry["w_tiles"], entry["h_tiles"])
                    col_ok = self._color_ok(region_b[y:y + th, x:x + tw], r, msk)
                    score = float(res[y, x]) + (0.03 if geo_ok else 0.0) + (0.03 if col_ok else 0.0)
                    raw.append({"type": canon(canonical), "score": round(score, 3),
                                "box": (int(x + rx0), int(y + ry0), tw, th),
                                "w_tiles": entry["w_tiles"], "h_tiles": entry["h_tiles"]})
        raw.sort(key=lambda h: -h["score"])
        kept = []
        for h in raw:
            bx, by, bw, bh = h["box"]
            bcx, bcy = bx + bw / 2.0, by + bh / 2.0
            dup = False
            for k in kept:
                kx, ky, kw, kh = k["box"]
                rad = max(bw, bh, kw, kh) * nms_dist
                if (bcx - (kx + kw / 2.0)) ** 2 + (bcy - (ky + kh / 2.0)) ** 2 < rad * rad:
                    dup = True
                    break
            if not dup:
                kept.append(h)
        return kept[:180]

    def prior(self, gray_crop, box_wh):
        """Blob 级弱先验（不抬 conf），返回 [(type,score)]。"""
        rows = []
        for canonical in self.types:
            entry = self._rep_entry(canonical)
            if entry is None:
                continue
            img = self._img(entry)
            if img is None or img.shape[2] != 4:
                continue
                best = -1.0
                for k in (0.9, 1.05):
                    tw, th = max(8, int(box_wh[0] * k)), max(8, int(box_wh[1] * k))
                    if tw >= gray_crop.shape[1] or th >= gray_crop.shape[0]:
                        continue
                    r = cv2.resize(img, (tw, th), interpolation=cv2.INTER_AREA)
                    msk = (r[:, :, 3] > 40).astype(np.uint8) * 255
                    tg = cv2.cvtColor(r, cv2.COLOR_BGRA2GRAY)
                    res = cv2.matchTemplate(gray_crop, tg, cv2.TM_CCOEFF_NORMED, mask=msk)
                    best = max(best, float(np.nan_to_num(res).max()))
                if best >= 0.30:
                    rows.append((canon(canonical), round(best, 3)))
        rows.sort(key=lambda r: -r[1])
        return rows[:3]
