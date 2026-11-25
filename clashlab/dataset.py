# -*- coding: utf-8 -*-
"""数据集聚合与样本研究（clashlab.dataset）。

职责：
1. 把 out/farm/samples/*（每个样本一个目录：frame.png + meta.json）聚合成 dataset/index.json：
   每样本记录路径、标定 quad、建筑数、可用性判定、可研究性评分、阵型类别与算类别用的证据。
2. study：样本 → 建筑清单 → vision.buildings_to_sim / 自建 sim → study.build_study →
   落 study.png + study.json，并把 study_figure 回填进 index。

设计原则：
- 只调用既有接口（vision / study / analysis / planner / assets / sim），不改其它模块；
- 阵型类别、可研究性全部从数据算，不写死、不凭感觉；
- 任何异常（缺 meta、labels=null、quad 无效、目录不存在/为空）都记 issue、标 usable=false，
  脚本退出码恒为 0，绝不崩。

可被 cli.py 复用的函数：
- build_index(samples_dir, out_path=None, logger=print)
- study_sample(sample_id, index_path=None, out_dir="out/dataset_study", layout=None, logger=print)
- list_samples(index_path=None)
"""
import argparse
import json
import math
import os
from datetime import datetime
from pathlib import Path

from . import vision

# 研究门槛：少于这个数目的建筑，覆盖/盲区分析没有统计意义，不硬凑
MIN_BUILDINGS = 6
INDEX_VERSION = 1


# ---------------- 小工具 ----------------

def _root():
    return Path(__file__).resolve().parents[1]


def _read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path, obj):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def _rel(path, root=None):
    """转成相对项目根的正斜杠路径，便于跨机器搬运。"""
    root = Path(root or _root())
    try:
        return os.path.relpath(path, root).replace("\\", "/")
    except ValueError:
        return str(path)


def _valid_quad(quad):
    """quad 必须是 4 个有限坐标点，且两条对角线都非退化。"""
    if not isinstance(quad, list) or len(quad) != 4:
        return False
    pts = []
    for p in quad:
        if not isinstance(p, (list, tuple)) or len(p) != 2:
            return False
        try:
            x, y = float(p[0]), float(p[1])
        except (TypeError, ValueError):
            return False
        if not (math.isfinite(x) and math.isfinite(y)):
            return False
        pts.append((x, y))
    d1 = math.hypot(pts[0][0] - pts[2][0], pts[0][1] - pts[2][1])
    d2 = math.hypot(pts[1][0] - pts[3][0], pts[1][1] - pts[3][1])
    if min(d1, d2) < 2.0:
        return False
    if max(d1, d2) / min(d1, d2) > 3.5:
        return False
    return True


def _find_frame(sample_dir, meta):
    """定位 frame.png：优先样本目录内 frame.png，其次 meta.frame 指向的路径。"""
    sample_dir = Path(sample_dir)
    direct = sample_dir / "frame.png"
    if direct.exists():
        return str(direct)
    meta_frame = meta.get("frame") if isinstance(meta, dict) else None
    if meta_frame:
        if os.path.isabs(meta_frame) and os.path.exists(meta_frame):
            return meta_frame
        cand = _root() / meta_frame
        if cand.exists():
            return str(cand)
        cand2 = sample_dir / meta_frame
        if cand2.exists():
            return str(cand2)
    return None


# ---------------- 建筑清单归一 ----------------

def _collect_buildings(meta, layout=None):
    """从 meta.labels（LLM 标注）或外置 layout JSON 取建筑清单。

    返回 (buildings, source, label_model, notes)。每项建筑归一为
    {"type", "tile": [x, y], "conf"}；坐标不做任何编造。
    """
    notes = []
    buildings = []
    source = "none"
    label_model = (meta or {}).get("label_model")

    if layout:
        data = _read_json(layout)
        buildings = [dict(b) for b in data.get("buildings", [])]
        source = "layout_ref"
        notes.append(f"建筑清单来自外置布局文件 {os.path.basename(layout)}")
    elif isinstance(meta, dict) and isinstance(meta.get("labels"), list) and meta["labels"]:
        for b in meta["labels"]:
            if not isinstance(b, dict):
                continue
            tile = b.get("tile")
            if not (isinstance(tile, (list, tuple)) and len(tile) == 2):
                continue
            buildings.append({
                "type": b.get("type") or "defense",
                "tile": [float(tile[0]), float(tile[1])],
                "conf": b.get("conf"),
            })
        source = "labels"
        label_model = meta.get("label_model") or label_model

    # 坐标清洗：越界剔除并记一笔，不回写原 meta
    clean = []
    for b in buildings:
        x, y = b["tile"]
        if not (0 <= x <= 44 and 0 <= y <= 44):
            notes.append(f"剔除越界建筑 {b['type']} @ ({x:.1f},{y:.1f})")
            continue
        b["tile"] = [int(round(x)), int(round(y))]
        clean.append(b)
    return clean, source, label_model, notes


# ---------------- 阵型类别（全部由坐标分布计算） ----------------

def _layout_metrics(buildings, n=44):
    """用建筑棋盘坐标算分布指标。中心 (n/2, n/2)，最远角距 ≈ n*sqrt(2)/2。"""
    if not buildings:
        return {"n": 0}
    cx = cy = n / 2.0
    corner_max = (n / 2.0) * math.sqrt(2)
    rs, dxys, xs, ys = [], [], [], []
    quads = [0, 0, 0, 0]  # NE NW SW SE
    corner_n = 0
    for b in buildings:
        x, y = b["tile"]
        dx, dy = x - cx, y - cy
        r = math.hypot(dx, dy)
        rs.append(r)
        dxys.append((dx, dy))
        xs.append(x)
        ys.append(y)
        if dx >= 0 and dy < 0:
            quads[0] += 1
        elif dx < 0 and dy < 0:
            quads[1] += 1
        elif dx < 0 and dy >= 0:
            quads[2] += 1
        else:
            quads[3] += 1
        if abs(dx) > n / 4.0 and abs(dy) > n / 4.0:
            corner_n += 1
    mean_r = sum(rs) / len(rs)
    var_r = sum((r - mean_r) ** 2 for r in rs) / len(rs)
    outer = sum(1 for r in rs if r / corner_max > 0.65) / len(rs)
    inner = sum(1 for r in rs if r / corner_max < 0.35) / len(rs)
    mid = 1.0 - outer - inner
    total = len(buildings)
    qshare = [q / total for q in quads]
    return {
        "n": total,
        "r_mean": round(mean_r, 2),
        "r_max": round(max(rs), 2),
        "r_std": round(math.sqrt(var_r), 2),
        "r_cv": round(math.sqrt(var_r) / mean_r, 3) if mean_r > 0 else 0.0,
        "outer_ratio": round(outer, 3),
        "mid_ratio": round(mid, 3),
        "inner_ratio": round(inner, 3),
        "quadrant_share": [round(s, 3) for s in qshare],
        "max_quad_share": round(max(qshare), 3),
        "corner_ratio": round(corner_n / total, 3),
        "bbox_span": [round(max(xs) - min(xs), 1), round(max(ys) - min(ys), 1)],
        "centroid_offset": [round(sum(xs) / total - cx, 1), round(sum(ys) / total - cy, 1)],
    }


def _classify_layout(ev):
    """按分布指标归类，返回 (类别名, 判定依据列表)。指标阈值写在这里、可追溯。"""
    n = ev.get("n", 0)
    if n == 0:
        return "unknown", ["无建筑坐标，无法归类"]
    reasons = []
    outer, inner = ev["outer_ratio"], ev["inner_ratio"]
    max_q = ev["max_quad_share"]
    corner = ev["corner_ratio"]
    cv = ev["r_cv"]

    if corner >= 0.35:
        reasons.append(f"角落集中度 {corner:.2f} ≥ 0.35")
        return "corner", reasons
    if outer >= 0.40 and inner <= 0.30 and max_q <= 0.38:
        reasons.append(f"外环占比 {outer:.2f} ≥ 0.40、内环 {inner:.2f} ≤ 0.30、四象限较均衡 {max_q:.2f}")
        return "ring", reasons
    if inner >= 0.45 and max_q <= 0.40:
        reasons.append(f"内环占比 {inner:.2f} ≥ 0.45、重心内聚")
        return "square", reasons
    if cv >= 0.55:
        reasons.append(f"半径变异系数 {cv:.2f} ≥ 0.55，远近分散")
        return "scatter", reasons
    reasons.append(f"外环 {outer:.2f}/内环 {inner:.2f}/角落 {corner:.2f} 均不占优，属混合")
    return "hybrid", reasons


# ---------------- 可研究性 ----------------

def _studyability(meta, quad_ok, n_buildings, conf, issues):
    """100 分起扣，返回 (0-100 整数, [扣分理由])。"""
    score = 100
    ded = []

    labels = (meta or {}).get("labels")
    if labels is None:
        score -= 40
        ded.append({"code": "labels_null", "points": 40,
                    "detail": "labels 为 null：无建筑标注，阵型无法计算"})
    elif not labels:
        score -= 40
        ded.append({"code": "labels_empty", "points": 40,
                    "detail": "labels 为空数组：无建筑标注"})

    if not quad_ok:
        score -= 30
        ded.append({"code": "quad_invalid", "points": 30,
                    "detail": "quad 缺失或非法：无有效地图标定"})

    if n_buildings == 0:
        score -= 35
        ded.append({"code": "no_buildings", "points": 35,
                    "detail": "可用于建模的建筑数为 0"})
    elif n_buildings < MIN_BUILDINGS:
        score -= 20
        ded.append({"code": "few_buildings", "points": 20,
                    "detail": f"建筑仅 {n_buildings} 个，少于 {MIN_BUILDINGS}，覆盖分析样本不足"})
    elif n_buildings < 10:
        score -= 8
        ded.append({"code": "sparse_buildings", "points": 8,
                    "detail": f"建筑 {n_buildings} 个（6-9），密度偏低"})

    if conf is not None:
        if conf < 0.15:
            score -= 20
            ded.append({"code": "conf_low", "points": 20,
                        "detail": f"边界标定置信度 {conf:.3f} < 0.15"})
        elif conf < 0.25:
            score -= 10
            ded.append({"code": "conf_mid", "points": 10,
                        "detail": f"边界标定置信度 {conf:.3f} < 0.25"})

    for it in (issues or []):
        score -= 4
        ded.append({"code": "meta_issue", "points": 4, "detail": str(it)[:80]})

    score = max(0, min(100, int(round(score))))
    return score, ded


# ---------------- index 构建 ----------------

def _analyze_sample(sample_dir, root=None, logger=print):
    """分析单个样本目录，返回 index 条目（不写盘）。"""
    root = Path(root or _root())
    sample_dir = Path(sample_dir)
    entry = {
        "id": sample_dir.name,
        "time": None,
        "frame": {"rel": None, "abs": None},
        "quad": None,
        "boundary": None,
        "buildings": {"count": 0, "source": "none", "label_model": None},
        "labels_source": None,
        "label_model": None,
        "issues": [],
        "usable": False,
        "usable_reason": "",
        "studyability": 0,
        "studyability_deductions": [],
        "layout_class": "unknown",
        "class_evidence": {"n": 0},
        "study_figure": None,
    }

    meta_path = sample_dir / "meta.json"
    meta = None
    if not meta_path.exists():
        entry["issues"].append("缺少 meta.json")
        entry["usable_reason"] = "缺少 meta.json，无法读取标定与标注"
        return entry
    try:
        meta = _read_json(meta_path)
    except Exception as e:
        entry["issues"].append(f"meta.json 解析失败: {str(e)[:80]}")
        entry["usable_reason"] = f"meta.json 解析失败: {str(e)[:60]}"
        return entry

    entry["id"] = meta.get("id") or sample_dir.name
    entry["time"] = meta.get("time")

    # frame 定位与可读性
    frame_abs = _find_frame(sample_dir, meta)
    probe = None
    if frame_abs is None:
        entry["issues"].append("找不到 frame.png")
        entry["usable_reason"] = "找不到 frame.png 画面文件"
    else:
        entry["frame"] = {"rel": _rel(frame_abs, root), "abs": str(Path(frame_abs).resolve())}
        probe = vision.imread(frame_abs)
        if probe is None:
            entry["issues"].append("frame.png 无法解码")
            entry["usable_reason"] = "frame.png 无法解码读取"

    # quad：meta.quad 优先，退回 meta.calib.quad
    quad = meta.get("quad")
    boundary = meta.get("calib") if isinstance(meta.get("calib"), dict) else None
    if boundary and not quad:
        quad = boundary.get("quad")
    quad_ok = _valid_quad(quad)
    if quad_ok:
        entry["quad"] = [[float(x), float(y)] for x, y in quad]
    else:
        entry["issues"].append("quad 缺失或非法")

    conf = None
    if boundary:
        conf = boundary.get("confidence")
        entry["boundary"] = {k: boundary.get(k) for k in ("source", "area_ratio", "ratio", "confidence")}

    # 建筑清单（index 阶段只统计数量与来源，不碰坐标编造）
    buildings, source, label_model, notes = _collect_buildings(meta)
    entry["issues"].extend(notes)
    entry["buildings"] = {"count": len(buildings), "source": source, "label_model": label_model}
    entry["labels_source"] = source
    entry["label_model"] = label_model

    # 阵型类别：有建筑坐标才算；否则 unknown
    ev = _layout_metrics(buildings) if buildings else {"n": 0}
    entry["class_evidence"] = ev
    entry["layout_class"], class_reasons = _classify_layout(ev)
    entry["issues"].extend(f"类别依据: {r}" for r in class_reasons)

    # 可用性：硬门槛——meta 可读、frame 可读、quad 有效、labels 非空
    reasons = []
    if not meta_path.exists():
        reasons.append("缺少 meta.json")
    if frame_abs is None:
        reasons.append("缺少画面 frame.png")
    elif probe is None:
        reasons.append("frame.png 损坏")
    if not quad_ok:
        reasons.append("quad 缺失或非法")
    if meta.get("labels") is None:
        reasons.append("labels 为 null：无建筑标注")
    elif not meta.get("labels"):
        reasons.append("labels 为空：无建筑标注")

    entry["usable"] = len(reasons) == 0
    entry["usable_reason"] = "；".join(reasons) if reasons else "meta/frame/quad/labels 齐全，可研究"

    # 可研究性评分
    score, ded = _studyability(meta, quad_ok, len(buildings), conf, meta.get("issues"))
    entry["studyability"] = score
    entry["studyability_deductions"] = ded
    if isinstance(meta.get("issues"), list):
        entry["issues"].extend(meta["issues"])
    return entry


def build_index(samples_dir, out_path=None, logger=print):
    """扫描 samples_dir 聚合 index；目录不存在/为空也返回合法 index，exit 0。"""
    root = _root()
    samples_dir = Path(samples_dir)
    if not samples_dir.is_absolute():
        candidates = [root / samples_dir, Path.cwd() / samples_dir]
        samples_dir = next((c for c in candidates if c.exists()), candidates[0])

    samples = []
    if not samples_dir.exists():
        logger(f"[index] 样本目录不存在: {samples_dir}（记为空索引，exit 0）")
    elif not samples_dir.is_dir():
        logger(f"[index] 样本路径不是目录: {samples_dir}")
    else:
        entries = sorted(p for p in samples_dir.iterdir() if p.is_dir())
        if not entries:
            logger(f"[index] 样本目录为空: {samples_dir}")
        for d in entries:
            try:
                entry = _analyze_sample(d, root=root, logger=logger)
            except Exception as e:  # 单样本失败不影响整批
                entry = {"id": d.name, "usable": False,
                         "usable_reason": f"分析异常: {str(e)[:80]}", "issues": [str(e)[:120]],
                         "layout_class": "unknown", "class_evidence": {"n": 0},
                         "studyability": 0, "studyability_deductions": []}
                logger(f"[index] {d.name} 分析异常: {e}")
            samples.append(entry)
            logger(f"[index] {entry['id']} usable={entry['usable']} "
                   f"buildings={entry['buildings']['count']} class={entry['layout_class']} "
                   f"studyability={entry['studyability']}")

    index = {
        "version": INDEX_VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "samples_dir": _rel(samples_dir, root),
        "count": len(samples),
        "samples": samples,
    }

    if out_path:
        out_path = Path(out_path)
        if not out_path.is_absolute():
            out_path = root / out_path
        _write_json(out_path, index)
        logger(f"[index] 写出 {out_path}（{len(samples)} 样本）")
    return index


# ---------------- study ----------------

def _sim_from_buildings(buildings, n=44):
    """建筑清单 → 模拟器（与 cli._sim_from_layout 同口径：类型取 assets.STATS）。"""
    from . import assets
    from .sim import Simulator
    sim = Simulator(n=n)
    for b in buildings:
        typ = b.get("type") or "defense"
        st = assets.STATS.get(typ, {})
        hp = b.get("hp", st.get("hp", 1400))
        dps = b.get("dps", st.get("dps", 120))
        rng = b.get("range", st.get("range", 9))
        sim.add_building(typ, b["tile"], hp, dps, rng)
    return sim


def _load_index(index_path=None):
    root = _root()
    if index_path is None:
        index_path = root / "dataset" / "index.json"
    index_path = Path(index_path)
    if not index_path.is_absolute():
        index_path = root / index_path
    return _read_json(index_path), index_path


def study_sample(sample_id, index_path=None, out_dir="out/dataset_study",
                 layout=None, logger=print):
    """单样本研究：建筑 → sim → build_study → study.png/study.json，回填 index。

    返回 {id, status, figure, reason, buildings}。status: ok / insufficient /
    unusable / missing。建筑不足标 insufficient，不硬造。
    """
    from . import planner, study as study_mod

    index, index_path = _load_index(index_path)
    rec = next((s for s in index.get("samples", []) if s.get("id") == sample_id), None)
    if rec is None:
        logger(f"[study] 样本 {sample_id} 不在索引中")
        return {"id": sample_id, "status": "missing", "figure": None,
                "reason": "索引中找不到该样本"}

    if not rec.get("usable"):
        logger(f"[study] {sample_id} 不可用: {rec.get('usable_reason')}")
        return {"id": sample_id, "status": "unusable", "figure": None,
                "reason": rec.get("usable_reason")}

    # 重新读 meta 拿建筑坐标（index 不存坐标）
    root = _root()
    meta_path = root / rec["frame"]["rel"]
    meta_dir = meta_path.parent
    meta_file = meta_dir / "meta.json"
    meta = _read_json(meta_file) if meta_file.exists() else {}

    buildings, source, label_model, notes = _collect_buildings(meta, layout=layout)
    if len(buildings) < MIN_BUILDINGS:
        reason = (f"建筑仅 {len(buildings)} 个，少于 {MIN_BUILDINGS}，覆盖/盲区分析样本不足；"
                  f"需要补足带坐标的建筑标注后再研究（当前来源 {source}）")
        logger(f"[study] {sample_id} insufficient: {reason}")
        return {"id": sample_id, "status": "insufficient", "figure": None,
                "reason": reason, "buildings": len(buildings)}

    sim = _sim_from_buildings(buildings)
    army = dict(planner.DEFAULT_ARMY)
    sdir = Path(out_dir)
    if not sdir.is_absolute():
        sdir = root / sdir
    sdir = sdir / sample_id
    report, plans, fig = study_mod.build_study(sim, army, out_dir=str(sdir))

    study_json = {
        "sample_id": sample_id,
        "buildings_source": source,
        "label_model": label_model,
        "buildings": [{"type": b["type"], "tile": b["tile"]} for b in buildings],
        "army": army,
        "report": report,
        "plans": plans,
        "figure": _rel(fig, root),
        "notes": notes,
    }
    _write_json(sdir / "study.json", study_json)

    # 回填 index 的 study_figure
    rec["study_figure"] = _rel(fig, root)
    _write_json(index_path, index)
    logger(f"[study] {sample_id} ok -> {fig}")
    return {"id": sample_id, "status": "ok", "figure": _rel(fig, root),
            "reason": None, "buildings": len(buildings)}


def study_all(index_path=None, out_dir="out/dataset_study", layout=None, logger=print):
    """批量研究所有可用样本；不可用/不足的记录原因，整体不中断。"""
    index, _ = _load_index(index_path)
    results = []
    for rec in index.get("samples", []):
        sid = rec["id"]
        if not rec.get("usable"):
            logger(f"[study-all] {sid} 跳过: {rec.get('usable_reason')}")
            results.append({"id": sid, "status": "unusable",
                            "reason": rec.get("usable_reason")})
            continue
        r = study_sample(sid, index_path=index_path, out_dir=out_dir,
                        layout=layout, logger=logger)
        results.append(r)
    return results


# ---------------- ls ----------------

def list_samples(index_path=None, usable_only=False):
    """返回样本摘要列表；CLI 打印表格。"""
    index, _ = _load_index(index_path)
    rows = []
    for s in index.get("samples", []):
        if usable_only and not s.get("usable"):
            continue
        rows.append({
            "id": s["id"],
            "time": s.get("time"),
            "usable": s.get("usable"),
            "reason": s.get("usable_reason"),
            "buildings": s["buildings"]["count"],
            "class": s.get("layout_class"),
            "studyability": s.get("studyability"),
            "study_figure": s.get("study_figure"),
        })
    return rows


# ---------------- CLI ----------------

def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m clashlab.dataset",
                                 description="部落冲突样本数据集聚合与研究")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_idx = sub.add_parser("index", help="扫描样本目录生成 index.json")
    p_idx.add_argument("--samples", required=True, help="样本目录，如 out/farm/samples")
    p_idx.add_argument("--out", default="dataset/index.json", help="index.json 输出路径")

    p_st = sub.add_parser("study", help="样本 → 研究图")
    p_st.add_argument("--id", help="样本 id")
    p_st.add_argument("--all", action="store_true", help="批量研究全部可用样本")
    p_st.add_argument("--out", default="out/dataset_study", help="研究产物目录")
    p_st.add_argument("--index", default=None, help="index.json 路径")
    p_st.add_argument("--layout", default=None, help="可选外置布局 JSON（覆盖 labels）")

    p_ls = sub.add_parser("ls", help="列出样本")
    p_ls.add_argument("--index", default=None, help="index.json 路径")
    p_ls.add_argument("--usable", action="store_true", help="只看可用样本")

    args = ap.parse_args(argv)

    if args.cmd == "index":
        build_index(args.samples, out_path=args.out)
    elif args.cmd == "study":
        if args.all:
            study_all(index_path=args.index, out_dir=args.out, layout=args.layout)
        elif args.id:
            study_sample(args.id, index_path=args.index, out_dir=args.out,
                         layout=args.layout)
        else:
            print("study 需要 --id <样本id> 或 --all")
            return 2
    elif args.cmd == "ls":
        rows = list_samples(args.index, usable_only=args.usable)
        print(f"{'id':<28} {'usable':<7} {'bld':>3} {'class':<9} {'study':>5}  reason")
        for r in rows:
            print(f"{r['id']:<28} {str(r['usable']):<7} {r['buildings']:>3} "
                  f"{r['class']:<9} {r['studyability']:>5}  {r['reason']}")
        print(f"共 {len(rows)} 条")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
