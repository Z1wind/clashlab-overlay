# -*- coding: utf-8 -*-
"""snap 编排：村庄截图 → 候选 json + 叠加图（识别引擎，不做界面、不做打法）。

第二轮管线：
1. 自校准（草地轮廓四角，不套旧参数）；
2. 三路分割独立出框（颜色/纹理/边缘），墙线单独提取不混建筑；
3. manifest 期望尺寸模板扫描 + 几何/颜色校验，全局 NMS 合并同址多框；
4. 置信度分档 high≥0.75 / review 0.45–0.75 / low<0.45。

确定性：阈值写死、无随机、键排序；created_at/elapsed 不参与一致性比较。
"""
import json
import math
import os
import time
from datetime import datetime, timezone

import cv2
import numpy as np
from PIL import Image, ImageDraw

from . import segment, calib as calib_mod
from .template_match import TemplateBank, canon

DETECTOR_VERSION = "snap-2.0.0"

COLOR_HIGH = (96, 200, 130)
COLOR_REVIEW = (240, 196, 82)
COLOR_LOW = (230, 96, 96)
SHORT_CN = {
    "town-hall": "大本", "eagle-artillery": "鹰炮", "scattershot": "散射",
    "inferno-tower": "地狱", "x-bow": "连弩", "cannon": "加农",
    "archer-tower": "箭塔", "wizard-tower": "法师", "air-defense": "防空",
    "mortar": "迫炮", "air-sweeper": "吹风", "hidden-tesla": "特斯拉",
    "bomb-tower": "炸弹", "spell-tower": "法塔", "multi-archer-tower": "多箭",
    "collector": "采集", "storage": "仓", "firespitter": "喷吐", "monolith": "巨石",
}


def _tile_px(calib):
    """单格边长估计：gx/gy 两轴边向量长度均值（欧氏），替代旧 L1 单轴粗估。"""
    p00 = calib.tile_to_px(0, 0)
    p10 = calib.tile_to_px(1, 0)
    p01 = calib.tile_to_px(0, 1)
    e1 = math.hypot(p10[0] - p00[0], p10[1] - p00[1])
    e2 = math.hypot(p01[0] - p00[0], p01[1] - p00[1])
    return max((e1 + e2) / 2.0, 1.0)


def _resolve_calib(frame, grid, calib_override):
    """解析标定：已验证参考标定优先，否则草地轮廓自检测 quad。

    calib_override:
      - {"quad": [[x,y]x4]}  已验证四角，走 Calib.from_quad；
      - {"H": [[...]]}        已验证单应，走 Calib.from_dict；
      - {"anchors": [...]}    已确认 (tile,px) 对，走 Calib.from_anchors 拟合。
    override 不做几何自检（由调用方保证已验证）；自检结果写入 boundary 供下游。
    """
    from .geo import Calib
    if calib_override:
        if "H" in calib_override:
            return Calib.from_dict(calib_override), {"method": "override:H", "calib_source": "verified"}
        if "quad" in calib_override:
            return Calib.from_quad(calib_override["quad"], n=grid), {"method": "override:quad", "calib_source": "verified"}
        if "anchors" in calib_override:
            return Calib.from_anchors(calib_override["anchors"], n=grid), {"method": "override:anchors", "calib_source": "verified"}
    calib, cmeta = calib_mod.detect_village_quad(frame, grid)
    cmeta = dict(cmeta or {})
    cmeta["calib_source"] = "auto"
    return calib, cmeta


def _iou(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ix0, iy0 = max(ax, bx), max(ay, by)
    ix1, iy1 = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    iw, ih = max(0, ix1 - ix0), max(0, iy1 - iy0)
    inter = iw * ih
    union = aw * ah + bw * bh - inter
    return float(inter) / float(union) if union > 0 else 0.0


def _nms(rows, iou_thr=0.30, center_scale=1.15):
    """贪心 NMS：按 conf 降序，抑制 IoU 高或中心过近的同址框，保留最高 conf。"""
    rows = sorted(rows, key=lambda r: -r["conf"])
    kept = []
    for r in rows:
        bx, by, bw, bh = r["box_px"]
        bcx, bcy = bx + bw / 2.0, by + bh / 2.0
        dup = False
        for k in kept:
            if _iou(r["box_px"], k["box_px"]) > iou_thr:
                dup = True
                break
            kx, ky, kw, kh = k["box_px"]
            rad = max(bw, bh, kw, kh) * center_scale
            if (bcx - (kx + kw / 2.0)) ** 2 + (bcy - (ky + kh / 2.0)) ** 2 < rad * rad:
                dup = True
                break
        if not dup:
            kept.append(r)
    return kept


def _template_conf(score):
    # 0.62→0.30(low) 0.75→0.55(review) 0.90→0.85(high)，弱命中不进 high
    return round(min(1.0, 0.30 + 0.70 * max(0.0, (score - 0.62) / 0.28)), 3)


def run_snap(image, out_dir, name=None, min_conf=0.75, grid=44, asset_root=None,
             freeze=None, use_templates=True, review_low=0.45, calib_override=None):
    t0 = time.perf_counter()
    frame = cv2.imdecode(np.fromfile(image, dtype=np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise SystemExit(f"读不到图片：{image}")
    fh, fw = frame.shape[:2]
    name = name or os.path.splitext(os.path.basename(image))[0]

    # 1) 校准：已验证参考标定(quad/H/anchors)优先；否则草地轮廓自检测 quad
    calib, cmeta = _resolve_calib(frame, grid, calib_override)
    if calib is None:
        raise SystemExit("边界标定失败：未取得可用 Calib（可经 calib_override 传入已验证标定）")
    tile_px = _tile_px(calib)
    sanity_ok, sanity_reasons = calib.sanity(frame.shape)
    # 自动 quad 几何自检拦不住「落在画面另一区域」的区域选错，故默认不采信；
    # 仅已验证来源（quad/H/anchors override）才允许把 tile 写进候选。
    # 未采信时只出 box_px（位置提示），不盖错格号。
    calib_trusted = cmeta.get("calib_source") == "verified"
    boundary = {"method": cmeta.get("method"), "quad": cmeta.get("quad"),
                 "source": cmeta.get("source"), "confidence": cmeta.get("confidence"),
                 "calib_source": cmeta.get("calib_source"),
                 "calib_sanity": {"ok": bool(sanity_ok), "reasons": sanity_reasons},
                 "calib_trusted": bool(calib_trusted)}
    if boundary["quad"] is None and calib.quad is not None:
        boundary["quad"] = calib.quad.tolist()

    # 2) 三路分割提案（独立于模板）；颜色团块为空时退到边缘密度格提案
    bm, wall = segment.proposal_masks(frame)
    blobs = segment.extract_blobs(bm)
    if not blobs:
        blobs = segment.cell_proposal(frame, tile_px)
    walls = segment.extract_walls(wall)

    # 3) 模板扫描：仅防空塔（air-defense）一类做位置提示，其余类型一律交人工
    bank = TemplateBank(asset_root, use_templates=use_templates)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    all_hits = bank.scan(gray, frame, tile_px) if use_templates else []
    hits = [h for h in all_hits if h["type"] == "air-defense"]

    rows = []
    for h in hits:
        bx, by, bw, bh = h["box"]
        rows.append({
            "type_guess": h["type"],
            "type_candidates": [{"type": h["type"], "conf": h["score"]}],
            "conf": _template_conf(h["score"]),
            "box_px": [int(bx), int(by), int(bw), int(bh)],
            "w_tiles": h["w_tiles"], "h_tiles": h["h_tiles"],
            "source": "template",
        })

    # 分割 blob 去重挂到模板框上，未被覆盖的作为位置提示候选（类型留空，交人工）
    hit_boxes = [r["box_px"] for r in rows]
    for blob in blobs:
        bx, by, bw, bh = blob["box"]
        if any(_iou((bx, by, bw, bh), hb) > 0.25 for hb in hit_boxes):
            continue
        rows.append({
            "type_guess": None,
            "type_candidates": [],
            "conf": 0.30,
            "box_px": [int(bx), int(by), int(bw), int(bh)],
            "w_tiles": None, "h_tiles": None,
            "source": "segment",
        })

    # 4) 全局 NMS + 坐标换算 + 分档
    rows = _nms(rows)
    for r in rows:
        bx, by, bw, bh = r["box_px"]
        if calib_trusted:
            gx, gy = calib.px_to_tile(bx + bw / 2.0, by + bh * 0.78)
            r["tile"] = [round(float(gx), 1), round(float(gy), 1)]
            r["size_tiles"] = int(np.clip(round(max(bw, bh) / tile_px), 1, 6))
        else:
            # 标定未验证：不写格坐标/尺寸，只保留像素框（位置提示层面），避免盖错格号
            r["tile"] = None
            r["size_tiles"] = None
        r["tier"] = "high" if r["conf"] >= min_conf else ("review" if r["conf"] >= review_low else "low")

    rows.sort(key=lambda r: (-r["conf"], r["box_px"][1], r["box_px"][0]))
    candidates = [r for r in rows if r["tier"] in ("high", "review")]
    low_zone = [r for r in rows if r["tier"] == "low"]

    elapsed = round(time.perf_counter() - t0, 3)
    all_conf = [r["conf"] for r in rows]
    stats = {
        "candidates_total": len(rows),
        "avg_conf": round(float(np.mean(all_conf)), 3) if all_conf else 0.0,
        "high": sum(1 for r in rows if r["tier"] == "high"),
        "review": sum(1 for r in rows if r["tier"] == "review"),
        "low_confidence": len(low_zone),
        "elapsed_seconds": elapsed,
        "proposal_mode": "segment+template" if use_templates else "segment_only",
        "templates_loaded": len(bank.types),
        "missing_types": bank.missing_types(),
        "walls_detected": len(walls),
        "template_prior": {
            "enabled": bool(use_templates),
            "scope": "air-defense only（其余类型交人工，模型不判类）",
            "hits": sum(1 for r in rows if r["source"] == "template"),
            "max_score": round(max((c["type_candidates"][0]["conf"] for c in rows if c["type_candidates"]), default=0.0), 3),
        },
        "boundary": boundary,
    }

    result = {
        "image": os.path.abspath(image),
        "grid": grid,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "detector_version": DETECTOR_VERSION,
        "position_only": True,
        "type_note": "type_guess 仅供人工下拉预选，模型不做类型判定；类型以人工 freeze retype 为准。",
        "asset_root": os.path.abspath(bank.root),
        "boundary": boundary,
        "stats": stats,
        "candidates": candidates,
        "low_confidence": low_zone,
    }

    out_dir = os.path.join(out_dir, name)
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "layout_candidates.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, sort_keys=True)

    overlay_path = os.path.join(out_dir, "overlay.png")
    _draw_overlay(frame, rows, overlay_path)

    grid_check_path = os.path.join(out_dir, "grid_check.png")
    cv2.imencode(".png", calib_mod.draw_grid(frame, calib))[1].tofile(grid_check_path)

    freeze_path = None
    if freeze:
        freeze_path = freeze
        frozen = _freeze_layout(result, name, grid)
        os.makedirs(os.path.dirname(os.path.abspath(freeze_path)) or ".", exist_ok=True)
        with open(freeze_path, "w", encoding="utf-8") as f:
            json.dump(frozen, f, ensure_ascii=False, indent=2, sort_keys=True)

    result["files"] = {"layout_candidates": json_path, "overlay": overlay_path,
                       "grid_check": grid_check_path, "freeze": freeze_path}
    return result


def _draw_overlay(frame, rows, path):
    img = Image.fromarray(frame[:, :, ::-1]).convert("RGBA")
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    from .render import font
    for r in rows:
        x, y, w, h = r["box_px"]
        col = {"high": COLOR_HIGH, "review": COLOR_REVIEW, "low": COLOR_LOW}[r["tier"]]
        d.rectangle([x, y, x + w, y + h], outline=col + (235,),
                    width=2 if r["tier"] != "low" else 1)
        label = SHORT_CN.get(r["type_guess"], "位置") if r.get("type_guess") else "位置"
        if r.get("tile"):
            txt = f"{label} {r['conf']:.2f} @{int(r['tile'][0])},{int(r['tile'][1])}"
        else:
            txt = f"{label} {r['conf']:.2f} [格坐标未标定]"
        d.rectangle([x, y - 15, x + len(txt) * 7, y - 1], fill=(12, 16, 20, 200))
        d.text((x + 3, y - 14), txt, font=font(11), fill=col + (255,))
    Image.alpha_composite(img, layer).convert("RGB").save(path)


def _freeze_layout(result, name, grid):
    """位置冻结骨架：只带格坐标/尺寸/置信度，不写 type（type_guess 仅供预选）。
    正式冻结走 clashlab.api freeze --edits-json retype 人工补类型。"""
    buildings = []
    for r in result["candidates"] + result["low_confidence"]:
        buildings.append({
            "tile": [int(round(r["tile"][0])), int(round(r["tile"][1]))] if r.get("tile") else None,
            "conf": r["conf"],
            "tier": r["tier"],
            "size_tiles": r["size_tiles"],
            "type_guess": r.get("type_guess"),
            "source": "snap",
        })
    return {
        "name": f"{name}_frozen",
        "grid": grid,
        "source": "snap",
        "note": "位置骨架：type_guess 仅供人工预选，不代表判定；正式冻结用 api freeze --edits-json retype 补类型。",
        "buildings": buildings,
        "walls": [],
    }
