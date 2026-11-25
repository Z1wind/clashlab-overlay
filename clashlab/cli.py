# -*- coding: utf-8 -*-
"""命令行入口：doctor / grab / analyze / demo / run / bench / plan"""
import argparse
import json
import os
import sys
import time
import traceback

import cv2

from . import __version__
from .config import Config, find_adb, find_ldconsole
from .adb import Adb
from . import vision, planner, render, demo as demo_mod, prompts


def _ensure_out(path):
    os.makedirs(path, exist_ok=True)
    return path


def _json(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


# ---------------- doctor ----------------
def cmd_doctor(args):
    cfg = Config().resolved()
    info = {"version": __version__, "python": sys.executable,
            "adb": cfg.adb, "ldconsole": cfg.ldconsole}
    try:
        adb = Adb(cfg.adb, args.serial)
        info["serial"] = adb.ensure_device()
        info["devices"] = adb.devices()
        info["wm_size"] = adb.wm_size()
        info["focus"] = adb.current_focus()
        info["coc_package"] = adb.find_coc()
        frame, ms, nbytes = adb.screencap()
        info["frame"] = {"size": [frame.shape[1], frame.shape[0]], "ms": round(ms, 1), "bytes": nbytes}
    except Exception as e:
        info["error"] = str(e)
    print(json.dumps(info, ensure_ascii=False, indent=2))
    return 0


# ---------------- analyze 单图 ----------------
def _analyze_image(path, n=44):
    frame = vision.imread(path)
    if frame is None:
        raise SystemExit(f"读不到图片：{path}")
    info, calib = vision.analyze_frame(frame, focus="com.supercell.clashofclans")
    return frame, info, calib


def _sim_from_layout(path, n=44):
    """从阵型 JSON 组装模拟器。布局优先级高于自动识别，误差最小。"""
    from . import assets
    from .sim import Simulator
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    sim = Simulator(n=n)
    for b in data.get("buildings", []):
        st = assets.STATS.get(b.get("type"), {})
        sim.add_building(b.get("type", "defense"), b["tile"],
                         b.get("hp", st.get("hp", 1400)),
                         b.get("dps", st.get("dps", 120)),
                         st.get("range", 9))
    walls = data.get("walls") or []
    if walls:
        sim.add_wall([tuple(w) for w in walls])
    return sim, data


def _build_from_image(frame, info, calib, thresh=0.5, layout=None):
    """识别建筑 → 组装模拟器 → 出计划。给了 layout 就用布局，跳过自动识别。"""
    dets = []
    if layout:
        sim, data = _sim_from_layout(layout)
        info["layout_source"] = os.path.basename(layout)
        info["buildings"] = [{"type": b["type"], "tile": b["tile"], "size": None}
                             for b in data.get("buildings", [])]
    else:
        dets, matches, dmeta = vision.scan_layout(frame, calib, thresh=thresh)
        info["detect"] = dmeta
        info["buildings"] = [
            {"type": d["type"], "tile": [round(d["tile"][0], 1), round(d["tile"][1], 1)],
             "size": d.get("stat", {}).get("size", d["size"]), "score": d["score"],
             "box": list(d["box"])} for d in dets
        ]
        sim = vision.buildings_to_sim(dets) if dets else None

    info.setdefault("detect", {})
    plan = None
    if sim is not None and calib is not None and sim.buildings:
        ring = vision.deployable_mask(calib, n=sim.n)
        plan = planner.build_plan(sim, ring, layout_id=info.get("state") or "live")
        ok, reasons = planner.validate(plan, sim, ring)
        info["plan_valid"] = ok
        info["plan_reasons"] = reasons
    return dets, plan


def cmd_analyze(args):
    frame, info, calib = _analyze_image(args.image, args.grid)
    dets, plan = _build_from_image(frame, info, calib, thresh=args.thresh, layout=args.layout)
    out = _ensure_out(args.out or "out")
    img = render.draw_overlay(frame, info, calib, plan)
    img = render.draw_hud(img, info, plan)
    render.save(img, os.path.join(out, "analyze.png"))
    _json(info, os.path.join(out, "analyze.json"))
    if plan:
        _json(plan, os.path.join(out, "plan.json"))
    print(json.dumps({"state": info["state"], "calib": (info["boundary"] or {}).get("source"),
                      "reproj": info["reproj"], "structures": len(dets),
                      "layout": info.get("layout_source"),
                      "typed": info.get("detect", {}).get("matched"), "plan": bool(plan),
                      "steps": len(plan["entry"]) if plan else 0,
                      "predicted": plan["predicted"] if plan else None,
                      "plan_valid": info.get("plan_valid"),
                      "elapsed_ms": plan["elapsed_ms"] if plan else None}, ensure_ascii=False))
    return 0


# ---------------- deploy 下发 ----------------
def cmd_deploy(args):
    """按计划点撒兵点。默认 dry-run，只有 --live 才真的点。"""
    cfg = Config().resolved()
    adb = Adb(cfg.adb, args.serial or cfg.serial)
    adb.ensure_device()
    with open(args.plan, "r", encoding="utf-8") as f:
        plan = json.load(f)
    frame, ms, _ = adb.screencap()
    info, calib = vision.analyze_frame(frame, focus=adb.current_focus())
    if calib is None:
        raise SystemExit("没有标定到地图，先抓一张能看清阵型的画面")
    sent = []
    for e in plan.get("entry", []):
        px, py = calib.tile_to_px(*e["tile"])
        sent.append({"step": e["step"], "tile": e["tile"], "px": [round(px, 1), round(py, 1)],
                     "count": e["count"], "dry_run": not args.live})
        if args.live:
            adb.tap(px, py, dry_run=False)
            time.sleep(args.gap)
    print(json.dumps({"live": bool(args.live), "latency_ms": round(ms, 1),
                      "taps": sent}, ensure_ascii=False, indent=2))
    return 0


# ---------------- annotate 半自动标注 ----------------
def cmd_annotate(args):
    from .annotate import run_annotate
    frame = vision.imread(args.image) if args.image else None
    if frame is None:
        cfg = Config().resolved()
        adb = Adb(cfg.adb, args.serial or cfg.serial)
        adb.ensure_device()
        frame, _, _ = adb.screencap()
        p = os.path.join(_ensure_out(args.out or "out"), f"annotate_{int(time.time())}.png")
        vision.imwrite(p, frame)
        args.image = p
    run_annotate(args.image, args.save)
    return 0


# ---------------- demo ----------------
def cmd_demo(args):
    out = _ensure_out(args.out or "out/demo")
    frame, sim, calib_true, quad = demo_mod.make_demo()

    info, calib = vision.analyze_frame(frame)
    err = None
    if calib is not None:
        d = [((calib.tile_to_px(*p)[0] - q[0]) ** 2 + (calib.tile_to_px(*p)[1] - q[1]) ** 2) ** 0.5
             for p, q in zip([(0, 0), (44, 0), (44, 44), (0, 44)], quad)]
        err = round(float(sum(d) / len(d)), 2)

    ring = demo_mod.ring_mask(sim.n)
    plan = planner.build_plan(sim, ring, layout_id="demo_th15")
    ok, reasons = planner.validate(plan, sim, ring)

    img = render.draw_overlay(frame, info, calib, plan)
    img = render.draw_hud(img, info, plan)
    render.save(img, os.path.join(out, "demo_hud.png"))
    render.save(render.draw_overlay(frame, info, calib, plan), os.path.join(out, "demo_overlay.png"))
    cv2.imwrite(os.path.join(out, "demo_base.png"), frame)

    report = {
        "detected_source": info["boundary"].get("source"),
        "confidence": round(info["boundary"].get("confidence", 0), 3),
        "calib_error_px": err,
        "reproj_px": info["reproj"],
        "state": info["state"],
        "plan_valid": ok,
        "plan_reasons": reasons,
        "plan": plan,
        "heat_top": plan["entry"] if plan else [],
        "sim_buildings": len(sim.buildings),
        "elapsed_ms": plan["elapsed_ms"] if plan else None,
    }
    _json(report, os.path.join(out, "report.json"))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


# ---------------- grab ----------------
def cmd_grab(args):
    cfg = Config().resolved()
    adb = Adb(cfg.adb, args.serial)
    adb.ensure_device()
    out = _ensure_out(args.out or "out")
    frame, ms, nbytes = adb.screencap()
    p = os.path.join(out, f"grab_{int(time.time())}.png")
    vision.imwrite(p, frame)
    info, calib = vision.analyze_frame(frame, focus=adb.current_focus())
    dets, plan = _build_from_image(frame, info, calib, thresh=args.thresh, layout=args.layout)
    img = render.draw_hud(render.draw_overlay(frame, info, calib, plan), info, plan)
    render.save(img, p.replace(".png", "_annotated.png"))
    print(json.dumps({"file": p, "ms": round(ms, 2), "bytes": nbytes,
                      "state": info["state"], "focus": info["focus"],
                      "boundary": info["boundary"].get("source"),
                      "reproj": info["reproj"], "structures": len(dets),
                      "typed": info["detect"].get("matched"),
                      "plan": bool(plan)}, ensure_ascii=False, indent=2))
    return 0


# ---------------- run ----------------
def cmd_run(args):
    cfg = Config().resolved()
    out = _ensure_out(args.out or "out/run")
    adb = Adb(cfg.adb, args.serial or cfg.serial)
    adb.ensure_device()
    coc = adb.find_coc()

    hud = None
    if args.hud:
        from .hud import Hud
        frame0, _, _ = adb.screencap()
        hud = Hud(frame0.shape[1], frame0.shape[0])

    states, lat, frames = [], [], 0
    plan = None
    recovered = 0
    t_end = time.time() + args.seconds
    last_save = 0.0
    last_plan = -1e9
    while time.time() < t_end:
        try:
            frame, ms, _ = adb.screencap()
        except Exception as e:
            print(f"[capture] {e}")
            time.sleep(1)
            continue
        frames += 1
        lat.append(ms)
        focus = adb.current_focus()
        info, calib = vision.analyze_frame(frame, focus=focus)
        info["coc_package"] = coc

        if info["state"] == "dialog":
            info["note"] = "检测到挂机/断线弹窗。"
            if args.recover and recovered < 3:
                btn = (info.get("dialog") or {}).get("reload_btn") or [int(frame.shape[1] * 0.305),
                                                                      int(frame.shape[0] * 0.642)]
                adb.tap(btn[0], btn[1], dry_run=False)
                recovered += 1
                info["note"] = f"检测到弹窗，已点击“重新载入游戏”@({btn[0]},{btn[1]})（第 {recovered} 次）。"
                time.sleep(2.5)

        # 阵型识别比较贵：状态为 base 时每 5 秒重算一次
        elif calib is not None and info["state"] in ("base", "deploy") and (time.time() - last_plan) > 5.0:
            dets, plan = _build_from_image(frame, info, calib, thresh=args.thresh, layout=args.layout)
            last_plan = time.time()
            info["note"] = (f"识别到 {len(dets)} 个地块，其中 {info['detect'].get('matched', 0)} 个已分类；"
                            f"按编号依次撒兵。" if plan else
                            (f"自动识别出 {len(dets)} 个候选地块，还不够出计划；用 annotate 补标注。"
                             if dets else "自动识别未就绪（0 个候选）。先跑 annotate 标注一次，再用 --layout 载入。"))
        elif calib is None:
            info["note"] = "未识别到战场外框：先保证画面上有完整阵型，或手动标定。"
        states.append(info["state"])

        if hud:
            hud.update_state(info, plan)

        now = time.time()
        if now - last_save >= max(1.0, args.save_every):
            annot = render.draw_overlay(frame, info, calib, plan)
            render.save(render.draw_hud(annot, info, plan, mini=not args.hud),
                        os.path.join(out, f"frame_{frames:03d}.png"))
            last_save = now

        time.sleep(max(0.0, args.interval - ms / 1000.0))

    report = {
        "frames": frames, "seconds": args.seconds,
        "fps": round(frames / max(args.seconds, 1e-6), 2),
        "adb_latency_ms_avg": round(sum(lat) / len(lat), 1) if lat else None,
        "adb_latency_ms_max": round(max(lat), 1) if lat else None,
        "states": {s: states.count(s) for s in set(states)},
        "recovered": recovered,
        "coc_package": coc,
        "hud_created": bool(hud),
        "out": out,
    }
    _json(report, os.path.join(out, "report.json"))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if hud:
        hud.root.after(600, hud.root.destroy)
        hud.run()
    return 0


# ---------------- snap 截图识别（新增子命令，不动已有命令） ----------------
def cmd_snap(args):
    from . import snap as snap_mod
    res = snap_mod.run_snap(
        args.image, args.out,
        name=args.name or None,
        min_conf=args.min_conf,
        grid=args.grid,
        asset_root=args.asset_root or None,
        freeze=args.freeze or None,
        use_templates=not args.no_templates,
    )
    print(json.dumps({
        "image": res["image"],
        "candidates": res["stats"]["candidates_total"],
        "high": res["stats"]["high"],
        "review": res["stats"]["review"],
        "low_confidence": res["stats"]["low_confidence"],
        "avg_conf": res["stats"]["avg_conf"],
        "elapsed_seconds": res["stats"]["elapsed_seconds"],
        "proposal_mode": res["stats"]["proposal_mode"],
        "files": res["files"],
    }, ensure_ascii=False, indent=2))
    return 0


# ---------------- bench ----------------
def cmd_bench(args):
    from .vdesk import run_bench
    cfg = Config().resolved()
    res = run_bench(seconds=args.seconds, serial=args.serial or "",
                    adb=cfg.adb, out=args.out or "out/bench",
                    cwd=os.getcwd(), desktop_name=args.desktop,
                    recover=args.recover, layout=args.layout)
    _json(res, os.path.join(args.out or "out/bench", "bench_result.json"))
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


# ---------------- study 离线策略研究 ----------------
def cmd_study(args):
    from . import analysis, study as study_mod
    sim, data = _sim_from_layout(args.layout, n=args.grid)
    army = dict(planner.DEFAULT_ARMY)
    if args.troops:
        army["troops"] = {"edrag": int(args.troops), "balloon": 0}
    report, plans, fig = study_mod.build_study(sim, army, out_dir=args.out or "out/study")
    _json({"layout": os.path.basename(args.layout), "army": army,
           "report": report, "plans": plans}, os.path.join(args.out or "out/study", "study.json"))
    print(json.dumps({
        "layout": os.path.basename(args.layout),
        "buildings": len(sim.buildings),
        "core_cover_dps": report["core_cover_dps"],
        "centroid": report["centroid"],
        "best_sector": report["sectors"][0] if report["sectors"] else None,
        "exposed_top": report["exposed"][:2],
        "blind_top": report["blind"][:2],
        "plans": [{"id": p["id"], "name": p["name"], "predicted": p["predicted"],
                   "risk": p["risk"], "entries": p["entries"]} for p in plans],
        "figure": fig,
    }, ensure_ascii=False, indent=2))
    return 0


# ---------------- farm 侦察采样 ----------------
def cmd_farm(args):
    from . import farm as farm_mod
    return farm_mod.run_cli(args)


# ---------------- marks 屏幕绘制标注（转发 plan_marks） ----------------
def cmd_marks(args):
    from . import plan_marks
    return plan_marks.cmd_marks(args)


# ---------------- dataset 样本数据集（薄转发 dataset.py，不重复实现） ----------------
def cmd_dataset(args):
    from . import dataset as ds
    return ds.main(args.dataset_argv)


# ---------------- profile 英雄装备画像（薄转发 equipment.py） ----------------
def cmd_profile(args):
    from . import equipment
    if args.set:
        slot = args.set[0]
        eq_csv = args.set[1] if len(args.set) > 1 else ""
        if slot not in equipment.HERO_SLOTS:
            print(f"未知槽位 {slot}，可选：{', '.join(equipment.HERO_SLOTS)}")
            return 1
        # 默认不写 config/heroes.json（只读）；未显式 --path 时落到 out/marks/profile_set.json
        target = args.path or os.path.join("out", "marks", "profile_set.json")
        prof = equipment.load_profile(args.path) if args.path else equipment.default_profile()
        eids = [e.strip() for e in eq_csv.split(",") if e.strip()]
        prof.setdefault("heroes", {}).setdefault(slot, {})["equipment"] = eids
        equipment.save_profile(prof, target)
        print(f"[profile] {slot} 装备写为 {eids} -> {target}（未改 config/heroes.json）")
    prof = equipment.load_profile(args.path) if args.path else equipment.load_profile()
    missing = equipment.validate_profile(prof)
    rules = equipment.profile_rules(prof)
    print(json.dumps({"profile": prof, "missing_icons": missing,
                      "enabled": rules["enabled"], "disabled": rules["disabled"]},
                     ensure_ascii=False, indent=2))
    return 0


# ---------------- prebattle 赛前简报（转发 prebattle.py，缺模块兜底） ----------------
def cmd_prebattle(args):
    try:
        from . import prebattle as pb
    except Exception as e:  # 模块未就绪时不崩
        print(f"prebattle 未就绪：{e!r}")
        return 0
    return pb.run_cli(args.prebattle_argv)


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    # dataset / prebattle 整段转发给各自模块的 argparse（薄封装，不重复实现）
    if argv and argv[0] in ("dataset", "prebattle"):
        try:
            if argv[0] == "dataset":
                from . import dataset as ds
                return ds.main(argv[1:])
            from . import prebattle as pb
            return pb.run_cli(argv[1:])
        except Exception as e:  # 模块缺失/参数错误不拖垮主入口
            print(f"{argv[0]} 转发失败: {e!r}")
            return 1
    ap = argparse.ArgumentParser(prog="clashlab", description="部落冲突战术研究实验台 v0.1")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("doctor", help="环境体检")
    p.add_argument("--serial", default="")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("grab", help="抓一帧并分析")
    p.add_argument("--serial", default="")
    p.add_argument("--out", default="out")
    p.add_argument("--thresh", type=float, default=0.5)
    p.add_argument("--layout", default="")
    p.set_defaults(func=cmd_grab)

    p = sub.add_parser("analyze", help="分析本地图片")
    p.add_argument("image")
    p.add_argument("--out", default="out")
    p.add_argument("--grid", type=int, default=44)
    p.add_argument("--thresh", type=float, default=0.5)
    p.add_argument("--layout", default="")
    p.set_defaults(func=cmd_analyze)

    p = sub.add_parser("deploy", help="按计划下发撒兵点（默认 dry-run）")
    p.add_argument("--plan", required=True)
    p.add_argument("--serial", default="")
    p.add_argument("--gap", type=float, default=0.8)
    p.add_argument("--live", action="store_true")
    p.set_defaults(func=cmd_deploy)

    p = sub.add_parser("annotate", help="半自动标注阵型")
    p.add_argument("--image", default="")
    p.add_argument("--serial", default="")
    p.add_argument("--save", default="layouts/layout.json")
    p.add_argument("--out", default="out")
    p.set_defaults(func=cmd_annotate)

    p = sub.add_parser("study", help="离线策略研究：覆盖、弱侧、候选方案")
    p.add_argument("--layout", required=True)
    p.add_argument("--out", default="out/study")
    p.add_argument("--grid", type=int, default=44)
    p.add_argument("--troops", type=int, default=0, help="雷龙数量，默认取 7")
    p.set_defaults(func=cmd_study)

    p = sub.add_parser("demo", help="仿真阵型全链路")
    p.add_argument("--out", default="out/demo")
    p.set_defaults(func=cmd_demo)

    p = sub.add_parser("run", help="实时循环")
    p.add_argument("--seconds", type=float, default=15)
    p.add_argument("--interval", type=float, default=0.6)
    p.add_argument("--save-every", type=float, default=2.0)
    p.add_argument("--thresh", type=float, default=0.5)
    p.add_argument("--layout", default="")
    p.add_argument("--recover", action="store_true", help="检测到挂机弹窗时自动点重新载入")
    p.add_argument("--serial", default="")
    p.add_argument("--adb", default="")
    p.add_argument("--out", default="out/run")
    p.add_argument("--hud", action="store_true")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("farm", help="侦察采样循环（默认 dry-run，--live 才真点；sample 模式不进攻）")
    p.add_argument("--rounds", type=int, default=6, help="循环轮数，默认 6")
    p.add_argument("--live", action="store_true", help="真点（默认 dry-run，不下发点击）")
    p.add_argument("--out", default="out/farm", help="输出目录，默认 out/farm")
    p.add_argument("--anchors", default="config/anchors.json", help="锚点文件，默认 config/anchors.json（缺失自动回落默认）")
    p.add_argument("--mode", default="sample", choices=["sample", "attack"], help="采样模式，默认 sample")
    p.add_argument("--grid", type=int, default=44, help="标定网格，默认 44")
    p.add_argument("--serial", default="", help="ADB 序列号，默认 127.0.0.1:5555")
    p.set_defaults(func=cmd_farm)

    p = sub.add_parser("marks", help="屏幕绘制标注：规则草案 + 模型补丁 → draw_calls")
    p.add_argument("--layout", required=True, help="阵型 JSON 路径")
    p.add_argument("--profile", default="", help="英雄装备画像 JSON（config/heroes.json）")
    p.add_argument("--style", default="terse", choices=list(prompts.STYLES.keys()))
    p.add_argument("--prebattle", default="", help="赛前 info.json（out/prebattle/info.json）")
    p.add_argument("--no-llm", action="store_true", help="跳过模型，纯规则")
    p.add_argument("--out", default="out/marks")
    p.add_argument("--model", default="", help="覆盖模型名；留空走默认回退链")
    p.add_argument("--grid", type=int, default=44)
    p.set_defaults(func=cmd_marks)

    p = sub.add_parser("dataset", help="样本数据集聚合/研究（转发 dataset.py）")
    p.add_argument("dataset_argv", nargs=argparse.REMAINDER)
    p.set_defaults(func=cmd_dataset)

    p = sub.add_parser("profile", help="查看/编辑英雄装备画像（转发 equipment.py）")
    p.add_argument("--show", action="store_true")
    p.add_argument("--set", nargs="+", metavar=("SLOT", "EQ"))
    p.add_argument("--path", default="", help="读写画像路径；默认只读 config/heroes.json，--set 不落原文件")
    p.set_defaults(func=cmd_profile)

    p = sub.add_parser("prebattle", help="赛前简报（转发 prebattle.py）")
    p.add_argument("prebattle_argv", nargs=argparse.REMAINDER)
    p.set_defaults(func=cmd_prebattle)

    p = sub.add_parser("snap", help="村庄截图 → 候选 json + 叠加图（离线识别引擎，不联网不调大模型）")
    p.add_argument("image", help="村庄俯视图路径")
    p.add_argument("--out", default="out/snap", help="输出根目录，默认 out/snap")
    p.add_argument("--name", default="", help="输出子目录名，默认取图片文件名")
    p.add_argument("--min-conf", type=float, default=0.5, help="高置信下限，默认 0.5")
    p.add_argument("--grid", type=int, default=44, help="标定网格，默认 44")
    p.add_argument("--asset-root", default="", help="建筑素材根目录，默认 assets/coc/buildings")
    p.add_argument("--freeze", default="", help="把 high/review 候选冻结为兼容 th13_sample 的 layout.json 路径")
    p.add_argument("--no-templates", action="store_true", help="禁用素材库弱先验（无底图对比跑用）")
    p.set_defaults(func=cmd_snap)

    p = sub.add_parser("bench", help="虚拟桌面隔离测试")
    p.add_argument("--seconds", type=float, default=10)
    p.add_argument("--serial", default="")
    p.add_argument("--out", default="out/bench")
    p.add_argument("--desktop", default="ClashLabBench")
    p.add_argument("--recover", action="store_true")
    p.add_argument("--layout", default="")
    p.set_defaults(func=cmd_bench)

    args = ap.parse_args(argv)
    if getattr(args, "adb", ""):
        os.environ["CLASHLAB_ADB"] = args.adb
    try:
        return args.func(args)
    except KeyboardInterrupt:
        return 130
    except Exception:
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
