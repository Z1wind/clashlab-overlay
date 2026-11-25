# -*- coding: utf-8 -*-
"""P3b-2 六阵连续墙线提取（候选，不改 bases/ 真数据）。

做什么
  1) 读取 tile->px 单应：优先 out/overlay/_quad_calib/summary.json 的 DLT H（02/03/05/06）；
     01/04 无像素对，退回 bases/th16/<NN>/notes.md §1 的包络 quad（Calib.from_quad 同语义）。
  2) 把 base.png 按 H 反投影到 44x44 栅格（默认 16px/tile）。
  3) 墙色阈值（明亮奶油白/低饱和）：HSV 里 V>=205 且 S<=70（阈值来自 06 的 k-means/直方图定标，
     见 out/overlay/_p3b/wall_repair_report.md §1）。
  4) 每格统计墙色像素占比 -> 候选墙格；剔除 layout.buildings 的 footprint 格；1 格定向补断。
  5) 输出 out/overlay/_p3b/walls_extracted/<NN>.json（walls + meta 阈值/检出格数/旧墙 Jaccard）。
  6) 用 clashlab.layout_score 的 analyze_compartments / wall_ring_coverage 算旧/新指标对照。

用法
  D:\Python313\python.exe tools/extract_walls.py --calibrate 06        # 阈值直方图定标
  D:\Python313\python.exe tools/extract_walls.py --bases 06           # 单阵
  D:\Python313\python.exe tools/extract_walls.py --all                # 六阵 + 指标 json
  D:\Python313\python.exe tools/extract_walls.py --all --overlays     # 另加叠加图
只读 bases/** 与 clashlab/**；只写 out/overlay/_p3b/**。
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys

import numpy as np
import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from clashlab.layout_score import (  # noqa: E402  只读复用，不改 clashlab
    analyze_compartments,
    footprint_bounds,
    size_of,
    wall_ring_coverage,
)

OUTDIR = os.path.join(ROOT, "out", "overlay", "_p3b")
WALLSDIR = os.path.join(OUTDIR, "walls_extracted")
TMPDIR = os.path.join(OUTDIR, "tmp")
BASES = ("01", "02", "03", "04", "05", "06")
GRID = 44
S = 16  # px per tile for the warped analysis raster

# 01/04 无 DLT 像素对（quad_report.md §2：硬解无意义）。这里照抄 notes.md §1 的包络 quad。
NOTES_QUAD = {
    "01": [[1180, 90], [2150, 480], [1180, 1180], [500, 480]],   # bases/th16/01/notes.md §1
    "04": [[1295, 10], [2205, 617], [1295, 1196], [386, 604]],   # bases/th16/04/notes.md §1
}

# ---- 墙色阈值（06 定标；见报告 §1）----
CREAM_V_MIN = 205
CREAM_S_MAX = 70
CELL_FRAC_MIN = 0.10   # 每格墙色像素占比阈值（主候选）
CREAM_CLOSED_FRAC_MIN = 0.08  # 连通增强变体的下限（形态学闭运算前）


def imread_u(path):
    """中文路径安全读图（cv2.imread 在 Windows 非 ASCII 路径会失败）。"""
    buf = np.fromfile(path, dtype=np.uint8)
    return cv2.imdecode(buf, cv2.IMREAD_COLOR)


def imwrite_u(path, img):
    ok, buf = cv2.imencode(".png", img)
    if not ok:
        raise RuntimeError("imencode failed: " + path)
    buf.tofile(path)


def resolve_H(name):
    """返回 (H 3x3, 来源说明)。优先 DLT H；否则由 notes quad 构造。"""
    sp = os.path.join(os.path.dirname(OUTDIR), "_quad_calib", "summary.json")
    if os.path.exists(sp):
        with open(sp, encoding="utf-8") as f:
            data = json.load(f)
        if name in data and data[name].get("H"):
            return np.array(data[name]["H"], dtype=np.float64), {
                "kind": "dlt_H",
                "source": "out/overlay/_quad_calib/summary.json",
                "n_train": data[name].get("n_train"),
                "train_p50_px": data[name].get("train_p50_px"),
                "tile_px_median": data[name].get("tile_px_median"),
            }
    if name in NOTES_QUAD:
        q = np.array(NOTES_QUAD[name], dtype=np.float32)
        src = np.array([[0, 0], [GRID, 0], [GRID, GRID], [0, GRID]], dtype=np.float32)
        H = cv2.getPerspectiveTransform(src, q)
        return H, {
            "kind": "quad_envelope",
            "source": "bases/th16/%s/notes.md §1" % name,
            "quad": NOTES_QUAD[name],
            "caveat": "无 DLT 像素对；包络 quad 标定，格位精度弱于 02/03/05/06（笔记自评 ±2~3 格）",
        }
    raise SystemExit("无单应来源: %s" % name)


def warp_to_grid(img, H, s=S):
    """tile 坐标（整数=格中心）-> s px/格 的栅格图。"""
    A = np.array([[s, 0, s / 2.0 - 0.5], [0, s, s / 2.0 - 0.5], [0, 0, 1]], dtype=np.float64)
    return cv2.warpPerspective(img, A @ np.linalg.inv(H), (GRID * s, GRID * s),
                               flags=cv2.INTER_LINEAR)


def wall_mask(warp_bgr):
    hsv = cv2.cvtColor(warp_bgr, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    return ((v >= CREAM_V_MIN) & (s <= CREAM_S_MAX)).astype(np.uint8)


def cell_fraction(mask, s=S):
    """44x44 每格墙色像素占比。"""
    return mask.reshape(GRID, s, GRID, s).mean(axis=(1, 3))


def building_cells(layout):
    """layout.buildings 的 footprint 格集合（与 layout_score 同口径）。"""
    cells = set()
    for b in layout.get("buildings") or []:
        if not b.get("tile"):
            continue
        x0, y0, w, h = footprint_bounds(b)
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                cells.add((x, y))
    return cells


def close_gaps(cells, grid=GRID):
    """定向补 1 格断点：左右都是墙或上下都是墙的空格补成墙。返回 (新集合, 补的格列表)。"""
    out = set(cells)
    added = []
    for y in range(grid):
        for x in range(grid):
            if (x, y) in out:
                continue
            lr = (x - 1, y) in out and (x + 1, y) in out
            ud = (x, y - 1) in out and (x, y + 1) in out
            if lr or ud:
                added.append((x, y))
    for c in added:
        out.add(c)
    return out, added


def jaccard(a, b):
    a, b = set(a), set(b)
    if not a and not b:
        return 1.0
    return len(a & b) / float(len(a | b))


def metrics_for(layout, walls, wall_cells):
    """旧/新两套墙数据的质量指标（用 clashlab.layout_score 同口径函数）。"""
    buildings = layout.get("buildings") or []
    grid = int(layout.get("grid", GRID))
    comp = analyze_compartments(grid, walls, buildings)
    comps = comp["compartments"]
    th = next((b for b in buildings if b.get("type") == "town-hall"), None)
    th_ring = wall_ring_coverage(th, walls, grid) if th is not None else None
    # 包围格命中（用于误检判断）：墙格与建筑 footprint 的重叠
    over_b = len(set(wall_cells) & building_cells(layout))
    return {
        "wall_count": comp["wall_count"],
        "isolated_wall_count": comp["isolated_wall_count"],
        "isolated_ratio": round(comp["isolated_wall_count"] / float(comp["wall_count"]), 4)
        if comp["wall_count"] else None,
        "th_tile": list(th["tile"]) if th else None,
        "th_ring_coverage": round(th_ring, 4) if th_ring is not None else None,
        "compartment_count": len(comps),
        "occupied_compartment_count": sum(1 for c in comps if c["building_ids"]),
        "dead_zone_count": sum(1 for c in comps if c["is_dead_zone"]),
        "dead_tiles": sum(c["tile_count"] for c in comps if c["is_dead_zone"]),
        "wall_on_building_footprint": over_b,
    }


def extract_base(name, make_overlay=False):
    layout_path = os.path.join(ROOT, "bases", "th16", name, "layout.json")
    with open(layout_path, encoding="utf-8") as f:
        layout = json.load(f)
    img_path = os.path.join(ROOT, "bases", "th16", name, "base.png")
    img = imread_u(img_path)
    if img is None:
        raise SystemExit("读图失败: " + img_path)

    H, hmeta = resolve_H(name)
    warp = warp_to_grid(img, H)
    mask = wall_mask(warp)
    frac = cell_fraction(mask)

    raw_cells = {(x, y) for y in range(GRID) for x in range(GRID) if frac[y, x] >= CELL_FRAC_MIN}
    bcells = building_cells(layout)
    kept = {c for c in raw_cells if c not in bcells}
    removed = sorted(raw_cells & bcells)
    # 主候选：1 格定向补断（左右或上下都是墙的空格补上）
    closed, added = close_gaps(kept)
    # 连通增强变体：低阈值 0.08 + 3x3 栅格闭运算（连接 1 格断点/拐角），仅供对照
    raw_lo = {(x, y) for y in range(GRID) for x in range(GRID) if frac[y, x] >= CREAM_CLOSED_FRAC_MIN}
    lo_kept = {c for c in raw_lo if c not in bcells}
    lo_mask = np.zeros((GRID, GRID), dtype=np.uint8)
    for (x, y) in lo_kept:
        lo_mask[y, x] = 1
    lo_mask = cv2.morphologyEx(lo_mask, cv2.MORPH_CLOSE, np.ones((3, 3), dtype=np.uint8))
    lo_cells = {(int(x), int(y)) for y, x in zip(*np.nonzero(lo_mask))}
    lo_cells, lo_added = close_gaps(lo_cells)

    old_walls = [(int(w[0]), int(w[1])) for w in (layout.get("walls") or [])]
    border_old = {(x, y) for x, y in old_walls if x in (0, GRID - 1) or y in (0, GRID - 1)}
    new_list = sorted(closed)
    border_new = {(x, y) for x, y in closed if x in (0, GRID - 1) or y in (0, GRID - 1)}

    meta = {
        "base": name,
        "source_image": "bases/th16/%s/base.png" % name,
        "grid": GRID,
        "homography": {
            "H": [[round(float(v), 8) for v in row] for row in H],
            **hmeta,
        },
        "warp_px_per_tile": S,
        "color_threshold": {
            "space": "HSV",
            "rule": "V>=%d and S<=%d (明亮奶油白/低饱和；金色侧面不作主判据)" % (CREAM_V_MIN, CREAM_S_MAX),
            "v_min": CREAM_V_MIN,
            "s_max": CREAM_S_MAX,
            "cell_fraction_min": CELL_FRAC_MIN,
            "calibration": "06 阵 k-means+HSV 直方图定标，见 wall_repair_report.md §1",
        },
        "counts": {
            "raw_cells": len(raw_cells),
            "removed_as_building_footprint": len(removed),
            "kept_before_gapfill": len(kept),
            "gap_filled": len(added),
            "detected_cells": len(closed),
            "closed_variant_cells": len(lo_cells),
            "closed_variant_threshold": CREAM_CLOSED_FRAC_MIN,
            "th16_max_walls_reference": 325,
        },
        "gap_filled_cells": [list(c) for c in added],
        "old_wall_count": len(old_walls),
        "jaccard_vs_old_all": round(jaccard(closed, old_walls), 4),
        "jaccard_vs_old_border": round(jaccard(border_new, border_old), 4),
        "old_recall": round(len(border_new & border_old) / float(len(border_old)), 4) if border_old else None,
        "run_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "notes": [
            "候选数据，未写入 bases/th16/*/layout.json；合入需 Lead 审核。",
            "建筑 footprint 格已剔除，但贴墙被建筑/装饰/水印遮挡的墙段可能漏检（见报告）。",
        ],
    }
    rec = {
        "base": name,
        "grid": GRID,
        "walls": [list(c) for c in new_list],
        "walls_closed_variant": [list(c) for c in sorted(lo_cells)],
        "meta": meta,
        "metrics": {
            "old": metrics_for(layout, old_walls, old_walls),
            "new": metrics_for(layout, new_list, new_list),
            "new_closed_variant": metrics_for(layout, sorted(lo_cells), sorted(lo_cells)),
        },
    }

    os.makedirs(WALLSDIR, exist_ok=True)
    outp = os.path.join(WALLSDIR, "%s.json" % name)
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)

    if make_overlay:
        os.makedirs(os.path.join(OUTDIR, "overlays"), exist_ok=True)
        ov = os.path.join(OUTDIR, "overlays", "%s_walls_overlay.png" % name)
        draw_overlay(name, layout, warp, closed, old_walls, ov)
    return rec


def draw_overlay(name, layout, warp, new_cells, old_walls, out_path, s=S):
    """原图(warp) + 检出墙高亮(绿) + 旧墙(红) + 建筑 footprint(黄)。"""
    vis = warp.copy()
    # 检出墙格：半透明绿填充
    layer = vis.copy()
    for (x, y) in new_cells:
        layer[y * s:(y + 1) * s, x * s:(x + 1) * s] = (60, 220, 60)
    vis = cv2.addWeighted(layer, 0.45, vis, 0.55, 0)
    for (x, y) in new_cells:
        cv2.rectangle(vis, (x * s, y * s), (x * s + s - 1, y * s + s - 1), (0, 160, 0), 1)
    # 建筑 footprint 黄框
    for b in layout.get("buildings") or []:
        if not b.get("tile"):
            continue
        x0, y0, w, h = footprint_bounds(b)
        cv2.rectangle(vis, (x0 * s + 2, y0 * s + 2), ((x0 + w) * s - 3, (y0 + h) * s - 3), (0, 230, 255), 1)
    # 旧墙红框
    for (x, y) in old_walls:
        cv2.rectangle(vis, (x * s + 3, y * s + 3), (x * s + s - 4, y * s + s - 4), (255, 0, 0), 1)
    cv2.putText(vis, "%s new=%d old=%d" % (name, len(new_cells), len(old_walls)), (8, 26),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    imwrite_u(out_path, vis)
    return out_path


def calibrate(name):
    """阈值定标：整图 HSV 直方图 + 每格 cream 占比分位 + 不同阈值的检出格数。"""
    with open(os.path.join(ROOT, "bases", "th16", name, "layout.json"), encoding="utf-8") as f:
        layout = json.load(f)
    img = imread_u(os.path.join(ROOT, "bases", "th16", name, "base.png"))
    H, hmeta = resolve_H(name)
    warp = warp_to_grid(img, H)
    print("[calibrate] base=%s H=%s" % (name, hmeta.get("kind")))
    hsv = cv2.cvtColor(warp, cv2.COLOR_BGR2HSV)
    cream = wall_mask(warp)
    print("  cream px %%: %.2f" % (100.0 * cream.mean()))
    # 12x4x4 HSV 直方图 top10
    flat = hsv.reshape(-1, 3).astype(np.int32)
    Hb, Sb, Vb = 12, 4, 4
    idx = ((flat[:, 0] * Hb // 180) * (Sb * Vb) + (flat[:, 1] * Sb // 256) * Vb
           + (flat[:, 2] * Vb // 256))
    cnt = np.bincount(idx, minlength=Hb * Sb * Vb)
    print("  top HSV bins (Hdeg/S/V_mid, px%, cumpx%):")
    cum = 0
    for t in np.argsort(cnt)[::-1][:10]:
        h = (t // (Sb * Vb)) * (180 // Hb) + (180 // Hb) // 2
        s = ((t % (Sb * Vb)) // Vb) * (256 // Sb) + (256 // Sb) // 2
        v = (t % Vb) * (256 // Vb) + (256 // Vb) // 2
        pct = 100.0 * cnt[t] / len(flat)
        cum += pct
        print("    H%3d S%3d V%3d  %5.2f%%  cum %5.2f%%" % (h * 2, s, v, pct, cum))
    frac = cell_fraction(cream)
    print("  cell frac percentiles:", np.percentile(frac, [50, 75, 90, 95, 97, 99]).round(3).tolist())
    for th in (0.05, 0.08, 0.10, 0.12, 0.15, 0.20, 0.25, 0.30):
        print("   frac>=%.2f -> %d cells (+%d after removing building footprints)"
              % (th, int((frac >= th).sum()),
                 len({(x, y) for y in range(GRID) for x in range(GRID)
                      if frac[y, x] >= th} - building_cells(layout))))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--bases", nargs="*", default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--calibrate", default=None)
    ap.add_argument("--overlays", action="store_true")
    ap.add_argument("--out-summary", default=os.path.join(WALLSDIR, "_metrics.json"))
    args = ap.parse_args(argv)

    if args.calibrate:
        calibrate(args.calibrate)
        return 0

    names = list(BASES) if args.all else (args.bases or ["06"])
    results = []
    for n in names:
        rec = extract_base(n, make_overlay=args.overlays)
        results.append(rec)
        o, nw = rec["metrics"]["old"], rec["metrics"]["new"]
        print("[%s] H=%s raw=%d kept=%d +gap=%d -> walls=%d | old walls=%d Jaccard=%.3f recall(border)=%s"
              % (n, rec["meta"]["homography"]["kind"], rec["meta"]["counts"]["raw_cells"],
                 rec["meta"]["counts"]["kept_before_gapfill"], rec["meta"]["counts"]["gap_filled"],
                 rec["meta"]["counts"]["detected_cells"], rec["meta"]["old_wall_count"],
                 rec["meta"]["jaccard_vs_old_all"], rec["meta"]["old_recall"]))
        nv = rec["metrics"]["new_closed_variant"]
        print("      TH ring  old=%s new=%s closed=%s | comps old=%d new=%d closed=%d | dead old=%d new=%d closed=%d"
              % (o["th_ring_coverage"], nw["th_ring_coverage"], nv["th_ring_coverage"],
                 o["compartment_count"], nw["compartment_count"], nv["compartment_count"],
                 o["dead_zone_count"], nw["dead_zone_count"], nv["dead_zone_count"]))

    os.makedirs(WALLSDIR, exist_ok=True)
    summary = {
        "generated_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "thresholds": {"CREAM_V_MIN": CREAM_V_MIN, "CREAM_S_MAX": CREAM_S_MAX,
                       "CELL_FRAC_MIN": CELL_FRAC_MIN, "warp_px_per_tile": S},
        "bases": {r["base"]: {"meta": {k: r["meta"][k] for k in
                                       ("homography", "counts", "jaccard_vs_old_all",
                                        "jaccard_vs_old_border", "old_recall", "old_wall_count")},
                              "metrics": r["metrics"]} for r in results},
    }
    if args.all:
        with open(args.out_summary, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=1)
        print("summary ->", args.out_summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
