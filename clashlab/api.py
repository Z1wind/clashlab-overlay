# -*- coding: utf-8 -*-
"""无窗口 API（覆盖层专用）：snap / freeze / prep 三条命令。

硬约束：本模块及其调用路径**不得 import tkinter**；stdout 只输出 JSON，
日志一律走 stderr 或日志文件，不污染 stdout。

函数入口（可被 Python 直接调用，返回同样的 JSON dict）：
    run_snap(image, out_dir="out/snap", thresh=0.5) -> dict
    run_freeze(candidates, edits=None, out_path="layouts/frozen.json",
               source="snap", base=None) -> dict
    run_prep(layout, out_dir="out/prep", profile="", enemy="") -> dict

CLI：
    python -m clashlab.api snap --image out/live_00.png [--out out/snap] [--thresh 0.5]
    python -m clashlab.api freeze --candidates out/snap/layout_candidates.json
        [--edits edits.json | --edits-json '{"add":[...]}'] --out layouts/frozen.json
    python -m clashlab.api prep --layout layouts/th13_sample.json [--out out/prep]
        [--profile config/heroes.json] [--enemy queen=75,king=75,cc=40]
"""
import argparse
import json
import logging
import os
import sys
import time
import traceback

GRID_N = 44

# 只做模块级 stdlib 导入；算法/识别模块一律函数内懒加载，避免链路带起重依赖。
LOG = logging.getLogger("clashlab.api")
logging.basicConfig(level=logging.INFO, stream=sys.stderr,
                    format="%(asctime)s [api] %(message)s")


# ---------------------------------------------------------------- 工具
def _err(code, msg, **extra):
    out = {"ok": False, "code": code, "msg": str(msg)}
    out.update(extra)
    return out


def _abs(p):
    return os.path.abspath(p) if p else p


def _read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(obj, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def _snap_tile(v):
    """吸附到 44 格整数网格，clamp 0..43。"""
    x, y = int(round(float(v[0]))), int(round(float(v[1])))
    return [max(0, min(GRID_N - 1, x)), max(0, min(GRID_N - 1, y))]


# ---------------------------------------------------------------- 命令 1：snap
def run_snap(image, out_dir="out/snap", thresh=0.5, overlay=True):
    """截图 → 候选建筑清单（tile/type/confidence）+ overlay.png。

    识别侧字段未冻结，raw 原始候选一并保留；归一化字段为 tile/type/confidence。
    """
    if not image or not os.path.exists(image):
        return _err("E_FILE_NOT_FOUND", f"图片不存在: {image}")
    try:
        from . import vision, render
    except Exception as e:
        return _err("E_MODULE_UNAVAILABLE", f"vision/render 模块不可用: {e!r}")

    frame = vision.imread(image)
    if frame is None:
        return _err("E_IMAGE_UNREADABLE", f"无法解码图片: {image}")

    try:
        info, calib = vision.analyze_frame(frame, focus="com.supercell.clashofclans")
    except Exception as e:
        return _err("E_BOUNDARY_FAILED", f"边界标定失败: {e!r}")

    if calib is None:
        return _err("E_BOUNDARY_LOW_CONFIDENCE",
                    "未标定到战场菱形（boundary confidence 过低），请换一张完整阵型截图",
                    boundary=info.get("boundary") or {}, state=info.get("state"))

    try:
        dets, matches, dmeta = vision.scan_layout(frame, calib, thresh=thresh)
    except Exception as e:
        return _err("E_SCAN_FAILED", f"建筑扫描失败: {e!r}")

    candidates = []
    for i, d in enumerate(dets):
        tile = [round(float(d["tile"][0]), 1), round(float(d["tile"][1]), 1)]
        candidates.append({
            "id": i,
            "tile": tile,
            "type": d.get("type") or None,
            "confidence": round(float(d.get("score") or 0.0), 3),
            "size": d.get("size"),
            "box": list(d.get("box") or []),
            "raw": {k: v for k, v in d.items() if k not in ("tile", "type", "score", "box")},
        })

    os.makedirs(out_dir, exist_ok=True)
    # overlay：复用 render.draw_overlay（只消费，不改识别）
    overlay_path = None
    if overlay:
        try:
            info["buildings"] = [{"type": c["type"], "box": c["box"]} for c in candidates]
            img = render.draw_overlay(frame, info, calib=calib)
            overlay_path = os.path.join(out_dir, "overlay.png")
            render.save(img, overlay_path)
        except Exception as e:
            LOG.warning("overlay 绘制失败（不影响候选输出）: %r", e)

    cand_path = os.path.join(out_dir, "layout_candidates.json")
    payload = {
        "ok": True,
        "cmd": "snap",
        "source_image": _abs(image),
        "frame_size": [int(frame.shape[1]), int(frame.shape[0])],
        "state": info.get("state"),
        "boundary": {
            "source": (info.get("boundary") or {}).get("source"),
            "confidence": (info.get("boundary") or {}).get("confidence"),
            "reproj": info.get("reproj"),
        },
        "detect_meta": dmeta,
        "candidates": candidates,
        "files": {
            "layout_candidates": _abs(cand_path),
            "overlay": _abs(overlay_path) if overlay_path else None,
        },
    }
    _write_json(payload, cand_path)
    LOG.info("snap: %d 候选 -> %s", len(candidates), cand_path)
    return payload


# ---------------------------------------------------------------- 命令 2：freeze
def _valid_type(t):
    from . import assets
    return t in assets.STATS


def run_freeze(candidates, edits=None, out_path="layouts/frozen.json",
               source="snap", base=None):
    """候选 + 编辑指令 → 合法 layout.json（44 格吸附 + 类型校验）。

    edits: {"add":[{"tile":[x,y],"type":...}],
            "remove":[{"tile":[x,y]}|{"idx":n}],
            "retype":[{"tile":[x,y],"type":...}]}
    输出沿用 th13_sample.json 结构：name/grid/note/buildings/walls，仅新增
    source/edits_applied/frozen_at 等新字段，不改既有字段语义。
    """
    if not candidates:
        return _err("E_NO_INPUT", "缺少候选清单")
    if isinstance(candidates, str):
        if not os.path.exists(candidates):
            return _err("E_FILE_NOT_FOUND", f"候选文件不存在: {candidates}")
        try:
            doc = _read_json(candidates)
        except Exception as e:
            return _err("E_JSON_PARSE", f"候选 JSON 解析失败: {e!r}")
        candidates = doc.get("candidates") or doc.get("buildings") or []
    if not isinstance(candidates, list):
        return _err("E_SCHEMA_INVALID", "候选清单必须是数组")

    # 基底：默认从候选建；可显式给 base layout（保留其 buildings/walls）
    buildings = []
    walls = []
    if base:
        if not os.path.exists(base):
            return _err("E_FILE_NOT_FOUND", f"base layout 不存在: {base}")
        try:
            bd = _read_json(base)
        except Exception as e:
            return _err("E_JSON_PARSE", f"base JSON 解析失败: {e!r}")
        buildings = [dict(b) for b in bd.get("buildings", [])]
        walls = [list(w) for w in (bd.get("walls") or [])]

    # 候选归一为 {type, tile}
    for c in candidates:
        if not isinstance(c, dict) or "tile" not in c:
            continue
        buildings.append({"type": c.get("type") or "defense",
                          "tile": _snap_tile(c["tile"])})

    edits = edits or {}
    if isinstance(edits, str):
        if not os.path.exists(edits):
            return _err("E_FILE_NOT_FOUND", f"编辑指令文件不存在: {edits}")
        try:
            edits = _read_json(edits)
        except Exception as e:
            return _err("E_JSON_PARSE", f"编辑指令 JSON 解析失败: {e!r}")
    edits = edits or {}

    applied = {"add": [], "remove": [], "retype": []}

    def _find(idx_or_tile):
        if isinstance(idx_or_tile, dict) and "idx" in idx_or_tile:
            i = int(idx_or_tile["idx"])
            return i if 0 <= i < len(buildings) else None
        if isinstance(idx_or_tile, dict) and "tile" in idx_or_tile:
            t = _snap_tile(idx_or_tile["tile"])
            for i, b in enumerate(buildings):
                if list(b["tile"]) == t:
                    return i
        return None

    for item in edits.get("remove") or []:
        i = _find(item)
        if i is None:
            return _err("E_TILE_NOT_FOUND", f"remove 目标不存在: {item}")
        applied["remove"].append(buildings.pop(i))

    for item in edits.get("retype") or []:
        i = _find(item)
        if i is None:
            return _err("E_TILE_NOT_FOUND", f"retype 目标不存在: {item}")
        t = item.get("type")
        if not _valid_type(t):
            return _err("E_UNKNOWN_TYPE", f"未知建筑类型 {t!r}，不在 assets.STATS")
        buildings[i]["type"] = t
        applied["retype"].append({"tile": buildings[i]["tile"], "type": t})

    for item in edits.get("add") or []:
        if "tile" not in item or "type" not in item:
            return _err("E_SCHEMA_INVALID", "add 项必须含 tile 与 type")
        t = item["type"]
        if not _valid_type(t):
            return _err("E_UNKNOWN_TYPE", f"未知建筑类型 {t!r}，不在 assets.STATS")
        tile = _snap_tile(item["tile"])
        if any(list(b["tile"]) == tile for b in buildings):
            return _err("E_TILE_CONFLICT", f"格 {tile} 已被占用，add 冲突")
        buildings.append({"type": t, "tile": tile})
        applied["add"].append({"tile": tile, "type": t})

    # 类型终检 + 坐标终检
    for b in buildings:
        if not _valid_type(b.get("type")):
            return _err("E_UNKNOWN_TYPE",
                        f"候选含未知类型 {b.get('type')!r}，请先用 retype 修正")
        tx, ty = b["tile"]
        if not (0 <= tx < GRID_N and 0 <= ty < GRID_N):
            return _err("E_TILE_OUT_OF_RANGE", f"格 {b['tile']} 越界（0..43）")

    layout = {
        "name": "frozen_layout",
        "grid": GRID_N,
        "note": "api.freeze 冻结产出；结构对齐 layouts/th13_sample.json",
        "source": source or "manual",
        "buildings": buildings,
        "walls": walls,
        "edits_applied": applied,
        "frozen_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    _write_json(layout, out_path)
    LOG.info("freeze: %d 建筑 -> %s", len(buildings), out_path)
    return {
        "ok": True, "cmd": "freeze",
        "buildings": len(buildings), "walls": len(walls),
        "edits_applied": applied,
        "files": {"layout": _abs(out_path)},
    }


# ---------------------------------------------------------------- 命令 3：prep
def _parse_enemy(enemy):
    if not enemy:
        return None
    out = {}
    for part in str(enemy).split(","):
        if "=" in part:
            k, v = part.split("=", 1)
            out[k.strip()] = v.strip()
    return out or None


def run_prep(layout, out_dir="out/prep", profile="", enemy=""):
    """冻结 layout → study / marks / prebattle 四件套。

    顺序（与算法侧约定一致）：
      sim, _ = cli._sim_from_layout(layout)
      ring = analysis.deployment_ring(sim)
      report, plans, _ = study.build_study(sim, army, ring, out_dir)
      marks = plan_marks.build_marks(sim, ring, report, plans, army,
                                      profile=..., cards=..., prebattle=info)
      info = prebattle.collect_info(...); brief = prebattle.brief(...)
    """
    if not layout or not os.path.exists(layout):
        return _err("E_FILE_NOT_FOUND", f"layout 不存在: {layout}")
    try:
        from . import analysis, study as study_mod, plan_marks, prebattle
        from . import planner, knowledge, equipment
        from .cli import _sim_from_layout
    except Exception as e:
        return _err("E_MODULE_UNAVAILABLE", f"算法模块不可用: {e!r}")

    os.makedirs(out_dir, exist_ok=True)
    army = dict(planner.DEFAULT_ARMY)

    # 1) sim / ring / study
    try:
        sim, _data = _sim_from_layout(layout, n=GRID_N)
    except Exception as e:
        return _err("E_SIM_FAILED", f"装载 layout 失败: {e!r}")
    if not sim.buildings:
        return _err("E_SCHEMA_INVALID", "layout 无建筑，无法研究")
    try:
        ring = analysis.deployment_ring(sim)
        report, plans, fig = study_mod.build_study(sim, army, ring, out_dir=out_dir)
    except Exception as e:
        return _err("E_STUDY_FAILED", f"study 失败: {e!r}")

    # 2) profile / cards / prebattle
    prof = None
    if profile:
        if not os.path.exists(profile):
            return _err("E_FILE_NOT_FOUND", f"profile 不存在: {profile}")
        try:
            prof = equipment.load_profile(profile)
        except Exception as e:
            return _err("E_PROFILE_FAILED", f"profile 读取失败: {e!r}")

    kb_brief = {"th": _data.get("th") or 13, "army": "edrag"}
    cards = []
    try:
        cards = knowledge.retrieve(profile=prof, brief=kb_brief, k=3)
    except Exception as e:
        LOG.warning("knowledge 检索失败（不阻塞）: %r", e)

    enemy_parsed = _parse_enemy(enemy)
    try:
        info = prebattle.collect_info(sim=sim, layout=layout, profile=prof,
                                      enemy=enemy_parsed)
        # brief 消费归一化 dict（id/title）；build_marks 要 [(card, reason)] 元组，分别传
        def _norm_card(c):
            src = c.get("source") or {}
            return {"id": c.get("id"),
                    "title": c.get("title") or src.get("title") or "",
                    "key_points": c.get("key_points") or []}
        cards_dicts = [_norm_card(c[0] if isinstance(c, tuple) else c) for c in cards]
        brief_text = prebattle.brief(report, plans, info, cards=cards_dicts)
    except Exception as e:
        return _err("E_PREBATTLE_FAILED", f"prebattle 失败: {e!r}")

    # 3) marks（规则链路，不调模型）
    try:
        marks = plan_marks.build_marks(sim, ring, report, plans, army,
                                       profile=prof, cards=cards, prebattle=info)
    except Exception as e:
        return _err("E_MARKS_FAILED", f"build_marks 失败: {e!r}")

    # 落盘四件套
    info_out = {k: v for k, v in info.items() if not k.startswith("_")}
    info_out["brief_chars"] = len(brief_text)
    info_out["cards"] = [(c[0] if isinstance(c, tuple) else c).get("id")
                         for c in cards]

    info_path = os.path.join(out_dir, "info.json")
    brief_path = os.path.join(out_dir, "brief.md")
    marks_path = os.path.join(out_dir, "marks.json")
    study_path = fig or os.path.join(out_dir, "study.png")

    try:
        _write_json(info_out, info_path)
        with open(brief_path, "w", encoding="utf-8") as f:
            f.write(brief_text + "\n")
        meta = {
            "layout": os.path.basename(layout),
            "profile_used": (marks.get("profile") or {}).get("used", []),
            "profile_missing": (marks.get("profile") or {}).get("missing", []),
            "cards": marks.get("cards") or [],
            "prebattle_loaded": True,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        _write_json({**marks, "meta": meta}, marks_path)
    except Exception as e:
        return _err("E_WRITE_FAILED", f"产物落盘失败: {e!r}")

    def _size(p):
        return os.path.getsize(p) if p and os.path.exists(p) else 0

    LOG.info("prep: study=%s marks=%s brief=%s info=%s",
              study_path, marks_path, brief_path, info_path)
    return {
        "ok": True, "cmd": "prep",
        "files": {
            "study_png": _abs(study_path),
            "marks_json": _abs(marks_path),
            "brief_md": _abs(brief_path),
            "info_json": _abs(info_path),
        },
        "sizes_bytes": {
            "study_png": _size(study_path),
            "marks_json": _size(marks_path),
            "brief_md": _size(brief_path),
            "info_json": _size(info_path),
        },
        "plans": [{"id": p.get("id"), "name": p.get("name"),
                   "predicted": p.get("predicted"), "risk": p.get("risk")}
                  for p in (plans or [])[:3]],
        "cards": meta["cards"],
    }


# ---------------------------------------------------------------- 命令 4：paths
def run_paths(layout="", out_dir="out/prep"):
    """读产物路径与存在性，不触发任何计算。"""
    files = {}
    for key, name in [("study_png", "study.png"), ("marks_json", "marks.json"),
                      ("brief_md", "brief.md"), ("info_json", "info.json")]:
        p = os.path.join(out_dir, name)
        exists = os.path.exists(p)
        files[key] = {
            "path": _abs(p),
            "exists": exists,
            "size_bytes": os.path.getsize(p) if exists else 0,
        }
    return {"ok": True, "cmd": "paths",
            "layout": _abs(layout) if layout else None,
            "files": files}


# ---------------------------------------------------------------- CLI
def main(argv=None):
    ap = argparse.ArgumentParser(prog="clashlab.api",
                                 description="无窗口 API：snap/freeze/prep，stdout 仅 JSON")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("snap", help="截图 → 候选清单 + overlay")
    p.add_argument("--image", required=True)
    p.add_argument("--out", default="out/snap")
    p.add_argument("--thresh", type=float, default=0.5)
    p.add_argument("--no-overlay", action="store_true")

    p = sub.add_parser("freeze", help="候选+编辑 → 合法 layout.json")
    p.add_argument("--candidates", required=True)
    p.add_argument("--edits", default="")
    p.add_argument("--edits-json", default="")
    p.add_argument("--out", default="layouts/frozen.json")
    p.add_argument("--source", default="snap")
    p.add_argument("--base", default="")

    p = sub.add_parser("prep", help="layout → study/marks/prebattle 四件套")
    p.add_argument("--layout", required=True)
    p.add_argument("--out", default="out/prep")
    p.add_argument("--profile", default="")
    p.add_argument("--enemy", default="")

    p = sub.add_parser("paths", help="读产物路径与存在性（不重算）")
    p.add_argument("--layout", default="")
    p.add_argument("--out", default="out/prep")

    args = ap.parse_args(argv)
    try:
        if args.cmd == "snap":
            res = run_snap(args.image, args.out, thresh=args.thresh,
                           overlay=not args.no_overlay)
        elif args.cmd == "freeze":
            edits = args.edits_json or args.edits or None
            res = run_freeze(args.candidates, edits=edits, out_path=args.out,
                             source=args.source, base=args.base or None)
        elif args.cmd == "paths":
            res = run_paths(args.layout, args.out)
        else:
            res = run_prep(args.layout, args.out, profile=args.profile,
                           enemy=args.enemy)
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        res = _err("E_INTERNAL", f"未捕获异常: {e!r}")

    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
