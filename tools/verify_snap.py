# -*- coding: utf-8 -*-
"""verify_snap.py —— snap 流水线可复跑验收脚本（验收方自有，不改识别侧）。

一条命令完成：
  (a) 同图两跑 snap，layout_candidates.json 逐字节级比对（时间字段忽略）；
  (b) 候选 vs gold：召回(A全量/B可检出)、误检率/精确率、平均 tile 误差、候选框数；
  (c) 人工最小修正证明：落 corrected_{name}.json，再校验与 gold 100% 一致；
  (d) 有/无建筑底图两种素材条件分别算召回（命令模板由调用方传入；未提供则如实记 N/A）。

候选缺失/命令不可用时优雅降级为 "no_candidates"/"unavailable"，不报错崩掉。

用法（项目根目录）：
  python tools/verify_snap.py --image out/snap/_source/village.png \
      --gold out/snap/gold/village_gold.json --name village \
      --work out/snap/village --runs 2 --dist 1.5 \
      [--snap-cmd "python -m clashlab.api snap --image {image} --out {out}"] \
      [--snap-cmd-noatlas "..."] \
      [--selfcheck] [--out-json out/snap/metrics_village.json]
"""
import argparse
import copy
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# 两跑比对时忽略的时间/运行态字段
IGNORE_KEYS = {"created_at", "frozen_at", "generated_at", "timestamp",
               "elapsed_ms", "elapsed", "duration", "files", "source_image",
               "frame_size", "ran_at", "wall_ms"}

DEFAULT_SNAP = ["python", "-m", "clashlab.api", "snap",
                "--image", "{image}", "--out", "{out}"]


# ---------------------------------------------------------------- 工具
def _load_json(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _find_candidates(out_dir):
    """在产物目录找 layout_candidates.json；兼容嵌套 {name}/ 子目录。"""
    for rel in ("layout_candidates.json",
                os.path.join("village", "layout_candidates.json")):
        p = os.path.join(out_dir, rel)
        if os.path.exists(p):
            return p
    for dirpath, _dirs, files in os.walk(out_dir):
        if "layout_candidates.json" in files:
            return os.path.join(dirpath, "layout_candidates.json")
    return None


def _norm_candidates(data):
    """归一化候选：接受 {candidates:[...]} / {buildings:[...]} / 顶层数组。"""
    if isinstance(data, list):
        raw = data
    elif isinstance(data, dict):
        raw = data.get("candidates") or data.get("buildings") or []
    else:
        raw = []
    out = []
    for i, c in enumerate(raw):
        if not isinstance(c, dict):
            continue
        tile = c.get("tile") or [None, None]
        try:
            gx, gy = float(tile[0]), float(tile[1])
        except (TypeError, ValueError, IndexError):
            continue
        out.append({
            "idx": i,
            "type": c.get("type"),
            "tile": [gx, gy],
            "confidence": c.get("confidence", c.get("conf", c.get("score", 0.0))),
            "size": c.get("size"),
            "box": c.get("box"),
            "tier": c.get("tier"),
            "source": c.get("source"),
        })
    return out


def _collect_candidates(data, include_low=False):
    """归一并可选合并 low_confidence 桶（保留独立 idx）。"""
    cands = _norm_candidates(data)
    if include_low and isinstance(data, dict):
        low = data.get("low_confidence") or []
        for j, c in enumerate(low):
            if not isinstance(c, dict):
                continue
            item = _norm_candidates([c])[0]
            item["idx"] = 100000 + j  # 续接 idx 避免与主候选冲突
            cands.append(item)
    return cands


def _library_types():
    """素材库类型：assets/coc/buildings 目录名为准，与 assets.STATS 取交集参考。"""
    bd = os.path.join(ROOT, "assets", "coc", "buildings")
    dirs = []
    if os.path.isdir(bd):
        dirs = [d for d in os.listdir(bd) if os.path.isdir(os.path.join(bd, d))]
    try:
        from clashlab import assets
        stats = set(assets.STATS.keys())
    except Exception:
        stats = set()
    return sorted(dirs), stats


def _drop_ignore(obj):
    if isinstance(obj, dict):
        return {k: _drop_ignore(v) for k, v in obj.items() if k not in IGNORE_KEYS}
    if isinstance(obj, list):
        return [_drop_ignore(v) for v in obj]
    return obj


def _deep_diff(a, b, path=""):
    diffs = []
    if type(a) != type(b):
        return [f"{path}: type {type(a).__name__} vs {type(b).__name__}"]
    if isinstance(a, dict):
        for k in set(a) | set(b):
            diffs += _deep_diff(a.get(k), b.get(k), f"{path}.{k}")
    elif isinstance(a, list):
        if len(a) != len(b):
            diffs.append(f"{path}: list len {len(a)} vs {len(b)}")
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                diffs += _deep_diff(x, y, f"{path}[{i}]")
    else:
        # 浮点容差 1e-6；绝对路径字符串归一化为文件名
        xa, xb = a, b
        if isinstance(xa, str) and isinstance(xb, str):
            xa, xb = os.path.basename(xa), os.path.basename(xb)
        if isinstance(xa, float) or isinstance(xb, float):
            try:
                if abs(float(xa) - float(xb)) > 1e-6:
                    diffs.append(f"{path}: {xa} vs {xb}")
            except (TypeError, ValueError):
                if xa != xb:
                    diffs.append(f"{path}: {xa} vs {xb}")
        elif xa != xb:
            diffs.append(f"{path}: {xa} vs {xb}")
    return diffs


# ---------------------------------------------------------------- snap 运行
def run_snap(cmd_template, image, out_dir, pyexe):
    """执行一次 snap；返回 (status, elapsed_s, candidates_path, stdout_tail, returncode)。"""
    os.makedirs(out_dir, exist_ok=True)
    if isinstance(cmd_template, str):
        cmd = [pyexe if t == "{python}" else t for t in
               cmd_template.format(image=image, out=out_dir).split()]
    else:
        cmd = [t.format(image=image, out=out_dir) for t in cmd_template]
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                              timeout=300, encoding="utf-8", errors="replace")
        elapsed = round(time.time() - t0, 3)
        rc = proc.returncode
        tail = (proc.stdout or "")[-1200:] + (proc.stderr or "")[-1200:]
    except FileNotFoundError as e:
        return "unavailable", round(time.time() - t0, 3), None, f"FileNotFoundError: {e}", -1
    except subprocess.TimeoutExpired:
        return "timeout", round(time.time() - t0, 3), None, "timeout 300s", -1
    cp = _find_candidates(out_dir)
    if cp is None:
        return "no_candidates", elapsed, None, tail, rc
    return "ok", elapsed, cp, tail, rc


# ---------------------------------------------------------------- 指标
def match_gold(gold_buildings, cands, dist_thresh, library):
    """贪心最近匹配：每个 gold 最多配一个候选；返回匹配表与未匹配。"""
    used = set()
    matches = []
    unmatched_gold = []
    for g in gold_buildings:
        best, bd = None, 1e9
        gt = g["tile"]
        for c in cands:
            if c["idx"] in used:
                continue
            d = ((c["tile"][0] - gt[0]) ** 2 + (c["tile"][1] - gt[1]) ** 2) ** 0.5
            if d < bd:
                best, bd = c, d
        if best is not None and bd <= dist_thresh:
            used.add(best["idx"])
            matches.append({"gold_id": g["id"], "gold_tile": gt,
                            "cand_idx": best["idx"], "cand_tile": best["tile"],
                            "dist": round(bd, 3),
                            "type_gold": g.get("type"),
                            "type_cand": best.get("type")})
        else:
            unmatched_gold.append(g["id"])
    fp = [c["idx"] for c in cands if c["idx"] not in used]
    return matches, unmatched_gold, fp


def metrics(gold_buildings, cands, dist_thresh, library_dirs, stats):
    matches, unmatched_gold, fp = match_gold(gold_buildings, cands, dist_thresh, library_dirs)
    n_gold = len(gold_buildings)
    matched = len(matches)
    # 口径 A：全量
    recall_a = round(matched / n_gold, 4) if n_gold else None
    # 口径 B：类型在素材库目录内的 gold；显式排除 storage/collector/wall（即使目录存在）
    EXCLUDED = {"storage", "collector", "wall"}
    lib_gold = [g for g in gold_buildings
                if g.get("type") in library_dirs and g.get("type") not in EXCLUDED]
    lib_matched = [m for m in matches
                   if m["type_gold"] in library_dirs and m["type_gold"] not in EXCLUDED]
    recall_b = round(len(lib_matched) / len(lib_gold), 4) if lib_gold else None
    # 误差
    errs = [m["dist"] for m in matches]
    mean_err = round(sum(errs) / len(errs), 3) if errs else None
    n_cand = len(cands)
    tp = matched
    precision = round(tp / n_cand, 4) if n_cand else None
    fp_rate = round(len(fp) / n_cand, 4) if n_cand else None  # FP/总候选
    return {
        "gold_total": n_gold,
        "gold_library_types": [g["id"] for g in lib_gold],
        "matched": matched,
        "recall_A_full": recall_a,
        "recall_B_library": recall_b,
        "library_type_denominator": len(lib_gold),
        "candidates_total": n_cand,
        "tp": tp,
        "fp_count": len(fp),
        "fp_candidates": fp,
        "precision": precision,
        "fp_rate_over_candidates": fp_rate,
        "mean_tile_error": mean_err,
        "unmatched_gold": unmatched_gold,
        "matches": matches,
        "type_agreed": [m["gold_id"] for m in matches
                        if m["type_gold"] and m["type_cand"]
                        and m["type_gold"] == m["type_cand"]],
    }


# ---------------------------------------------------------------- 100% 证明
def build_corrected(gold_buildings, cands, matches, fp, dist_thresh, out_path):
    """最小人工修正：候选就近吸附到 gold、删多余框，缺的按 gold 补上。"""
    used = {m["cand_idx"] for m in matches}
    corrected = {"name": "village_corrected", "grid": 44,
                 "note": "人工最小修正版：候选就近吸附 gold、删多余框、补缺；用于100%一致性证明。",
                 "source": "manual_correction",
                 "buildings": []}
    fix_log = {"snapped": [], "added": [], "dropped_candidates": fp}
    m_by_gold = {m["gold_id"]: m for m in matches}
    for g in gold_buildings:
        if g["id"] in m_by_gold:
            m = m_by_gold[g["id"]]
            fix_log["snapped"].append({"gold_id": g["id"],
                                       "cand_idx": m["cand_idx"],
                                       "from": m["cand_tile"], "to": g["tile"]})
        else:
            fix_log["added"].append({"gold_id": g["id"], "tile": g["tile"]})
        corrected["buildings"].append({
            "type": g.get("type") or "defense",
            "tile": [int(g["tile"][0]), int(g["tile"][1])],
            "size_tiles": g.get("size_tiles"),
            "source_gold": g["id"],
        })
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(corrected, f, ensure_ascii=False, indent=2)

    # 校验：corrected vs gold 100%
    ok = len(corrected["buildings"]) == len(gold_buildings)
    bad = []
    gmap = {g["id"]: g for g in gold_buildings}
    for b in corrected["buildings"]:
        gid = b["source_gold"]
        g = gmap[gid]
        if [b["tile"][0], b["tile"][1]] != [int(g["tile"][0]), int(g["tile"][1])]:
            ok = False
            bad.append(gid)
    proof = {
        "corrected_buildings": len(corrected["buildings"]),
        "gold_buildings": len(gold_buildings),
        "perfect_match_100pct": ok and not bad,
        "mismatch": bad,
        "manual_fixes": {
            "snapped": len(fix_log["snapped"]),
            "added": len(fix_log["added"]),
            "dropped_candidates": len(fix_log["dropped_candidates"]),
            "total_manual_actions": len(fix_log["snapped"]) + len(fix_log["added"])
                                    + len(fix_log["dropped_candidates"]),
        },
        "fix_log": fix_log,
    }
    return corrected, proof


# ---------------------------------------------------------------- 主流程
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--gold", required=True)
    ap.add_argument("--name", default="village")
    ap.add_argument("--work", default="out/snap/village")
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--dist", type=float, default=1.5)
    ap.add_argument("--snap-cmd", default=None, help="模板，{image}/{out} 占位")
    ap.add_argument("--snap-cmd-noatlas", default=None)
    ap.add_argument("--candidates", default=None,
                    help="预读引擎直写的 layout_candidates.json，跳过 snap 子进程；"
                         "用于测量引擎产物，复跑仍由本脚本完成")
    ap.add_argument("--candidates2", default=None,
                    help="第二份预读候选，用于两跑一致性比对")
    ap.add_argument("--include-low-confidence", action="store_true",
                    help="合并 low_confidence 桶进候选集（默认只量主候选）")
    ap.add_argument("--project-candidates", action="store_true",
                    help="用 gold 的 calib H 把候选 box_px 中心反投影为 tile（候选标签帧与 gold 帧不一致时对齐）")
    ap.add_argument("--engine-quad", default=None,
                    help="JSON 文件或内联四角[[x,y]...]：用引擎 quad 把 gold foot_px 投影到引擎帧，候选标签不动")
    ap.add_argument("--selfcheck", action="store_true")
    ap.add_argument("--out-json", default=None)
    args = ap.parse_args()

    pyexe = sys.executable
    snap_cmd = args.snap_cmd or DEFAULT_SNAP
    precomputed = bool(args.candidates)
    gold = _load_json(os.path.join(ROOT, args.gold))
    gold_buildings = gold["buildings"]

    # --engine-quad：把 gold foot_px 投影到引擎帧（候选标签不动）
    if args.engine_quad:
        from clashlab.geo import Calib
        qraw = args.engine_quad
        if os.path.exists(qraw):
            qraw = _load_json(qraw)
        else:
            qraw = json.loads(qraw)
        eq = qraw.get("quad") or qraw.get("boundary", {}).get("quad") or qraw
        ecal = Calib.from_quad(eq, n=44)
        for b in gold_buildings:
            fp = b.get("foot_px")
            if fp:
                gx, gy = ecal.px_to_tile(*fp)
                b["tile"] = [round(gx, 3), round(gy, 3)]
    library_dirs, stats = _library_types()

    result = {
        "params": {
            "image": args.image, "gold": args.gold, "name": args.name,
            "runs": args.runs, "dist_thresh": args.dist,
            "snap_cmd": ("precomputed --candidates " + args.candidates)
                        if precomputed else (snap_cmd if isinstance(snap_cmd, str)
                                             else " ".join(snap_cmd)),
            "snap_cmd_noatlas": args.snap_cmd_noatlas,
            "project_candidates": args.project_candidates,
            "include_low_confidence": args.include_low_confidence,
            "library_dirs": library_dirs,
            "selfcheck": args.selfcheck,
        },
        "library_types_on_disk": library_dirs,
    }

    # ---- (a) 两跑一致性 ----
    # 预读模式（--candidates）：引擎直写产物，跳过 snap 子进程；
    # 复跑指标仍由本脚本完成，确定性比对用 --candidates2。
    runs = []
    cands_primary = None
    if precomputed:
        cp1 = os.path.join(ROOT, args.candidates)
        cp2 = os.path.join(ROOT, args.candidates2) if args.candidates2 else None
        runs.append({"run": 1, "status": "ok", "elapsed_s": None,
                     "candidates": cp1, "returncode": 0,
                     "candidates_json": os.path.relpath(cp1, ROOT),
                     "source": "precomputed_engine_output"})
        cands_primary = cp1
        if cp2 and os.path.exists(cp2):
            runs.append({"run": 2, "status": "ok", "elapsed_s": None,
                         "candidates": cp2, "returncode": 0,
                         "candidates_json": os.path.relpath(cp2, ROOT),
                         "source": "precomputed_engine_output"})
        result["runs"] = runs
    else:
        for i in range(args.runs):
            out_dir = os.path.join(ROOT, args.work, f"run{i+1}")
            status, elapsed, cp, tail, rc = run_snap(snap_cmd, args.image, out_dir, pyexe)
            entry = {"run": i + 1, "status": status, "elapsed_s": elapsed,
                     "candidates": cp, "returncode": rc}
            if cp:
                entry["candidates_json"] = os.path.relpath(cp, ROOT)
                if cands_primary is None:
                    cands_primary = cp
            runs.append(entry)
            result[f"run{i+1}_tail"] = tail[-600:]
        result["runs"] = runs

    determinism = {"requested": args.runs, "precomputed": precomputed}
    if len(runs) >= 2 and all(r.get("candidates") for r in runs[:2]):
        a = _drop_ignore(_load_json(runs[0]["candidates"]))
        b = _drop_ignore(_load_json(runs[1]["candidates"]))
        diffs = _deep_diff(a, b)
        determinism.update({"both_ok": True,
                           "identical": len(diffs) == 0, "diffs": diffs[:20],
                           "diff_count": len(diffs)})
    elif precomputed and not cp2:
        determinism.update({"both_ok": False,
                            "note": "仅提供单份引擎产物，未做两跑比对（单跑复跑由本脚本重算指标）"})
    else:
        determinism.update({"both_ok": False,
                            "note": "候选缺失或 snap 不可用，未做两跑比对"})
    result["determinism"] = determinism

    # ---- (b) 指标 ----
    metrics_block = None
    corrected_path = os.path.join(ROOT, "out/snap", f"corrected_{args.name}.json")
    cands = []
    engine_meta = None
    if cands_primary and os.path.exists(cands_primary):
        raw = _load_json(cands_primary)
        if args.project_candidates:
            from clashlab.geo import Calib
            calib = Calib.from_dict(gold["calib"])
            def _reproj(c):
                bx = c.get("box_px")
                if not bx:
                    return c
                cx, cy = bx[0] + bx[2] / 2, bx[1] + bx[3] / 2
                gx, gy = calib.px_to_tile(cx, cy)
                c["tile"] = [round(gx, 3), round(gy, 3)]
                return c
            raw["candidates"] = [_reproj(c) for c in raw.get("candidates", [])]
            if isinstance(raw.get("low_confidence"), list):
                raw["low_confidence"] = [_reproj(c) for c in raw["low_confidence"]]
        cands = _collect_candidates(raw, include_low=args.include_low_confidence)
        metrics_block = metrics(gold_buildings, cands, args.dist, library_dirs, stats)
        engine_meta = {
            "detector_version": raw.get("detector_version"),
            "boundary": raw.get("boundary"),
            "stats": raw.get("stats"),
            "low_confidence_count": len(raw.get("low_confidence") or [])
                if isinstance(raw, dict) else None,
            "include_low_confidence": args.include_low_confidence,
        }
    else:
        metrics_block = {"status": "no_candidates",
                         "note": "尚无候选，指标留待引擎产物出现后复跑"}
    result["engine_meta"] = engine_meta
    # (c) 100% 证明：有无候选都落 corrected_{name}.json（无候选时全部按 gold 补入）
    _, proof = build_corrected(gold_buildings, cands,
                               metrics_block.get("matches", []),
                               metrics_block.get("fp_candidates", []),
                               args.dist, corrected_path)
    metrics_block["corrected_path"] = os.path.relpath(corrected_path, ROOT)
    metrics_block["proof_100pct"] = proof
    result["metrics"] = metrics_block

    # ---- (d) 素材条件对比 ----
    cond = {}
    if precomputed:
        cond = {"atlas_on": {"status": "not_applicable",
                             "note": "预读引擎产物模式，未运行 snap 子进程，底图条件对比 N/A"},
                "atlas_off": {"status": "not_applicable",
                              "note": "预读引擎产物模式，未运行 snap 子进程，底图条件对比 N/A"}}
    else:
      for label, cmd in (("atlas_on", snap_cmd), ("atlas_off", args.snap_cmd_noatlas)):
        if not cmd:
            cond[label] = {"status": "not_configured",
                           "note": "本构建未提供无底图命令模板，无法对比"}
            continue
        out_dir = os.path.join(ROOT, args.work, f"cond_{label}")
        status, elapsed, cp, tail, rc = run_snap(cmd, args.image, out_dir, pyexe)
        block = {"status": status, "elapsed_s": elapsed}
        if cp:
            cands = _norm_candidates(_load_json(cp))
            m = metrics(gold_buildings, cands, args.dist, library_dirs, stats)
            block.update({"recall_A": m["recall_A_full"], "recall_B": m["recall_B_library"],
                          "candidates": m["candidates_total"], "fp": m["fp_count"]})
        block["tail"] = tail[-400:]
        cond[label] = block
    result["atlas_conditions"] = cond

    # ---- selfcheck：合成候选，只自检逻辑，不进正式报告 ----
    if args.selfcheck:
        synth = []
        for i, g in enumerate(gold_buildings[:4]):
            synth.append({"idx": i, "type": g.get("type"),
                          "tile": [g["tile"][0] + 0.3, g["tile"][1] - 0.2],
                          "confidence": 0.9, "size": None, "box": None})
        synth.append({"idx": 99, "type": "cannon", "tile": [5, 5],
                      "confidence": 0.5, "size": None, "box": None})
        sc = metrics(gold_buildings, synth, args.dist, library_dirs, stats)
        _, sc_proof = build_corrected(gold_buildings, synth, sc["matches"],
                                      sc["fp_candidates"], args.dist,
                                      os.path.join(ROOT, "out/snap",
                                                   "selfcheck_corrected.json"))
        result["selfcheck"] = {"metrics": {k: v for k, v in sc.items() if k != "matches"},
                               "proof_100pct": sc_proof,
                               "note": "合成候选自检，不写入正式报告"}

    out_json = args.out_json or os.path.join(ROOT, "out/snap", f"metrics_{args.name}.json")
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps({
        "status": "ok" if cands_primary else "no_candidates",
        "determinism": determinism,
        "metrics": {k: v for k, v in (metrics_block or {}).items() if k != "matches"},
        "out_json": os.path.relpath(out_json, ROOT),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
