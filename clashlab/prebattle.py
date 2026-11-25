# -*- coding: utf-8 -*-
"""赛前简报：把「侦察截图 / 阵型 / 双方已知信息」压成结构化 info + ≤900 字简报。

设计原则：模型只据「已知 / 未知」出战术，不许想象。视觉识别目前不可用的数字
（TH 等级、敌方英雄等级、CC 兵种）一律 null 并写进 unknown，绝不猜。

对外 API（字段名固定，勿改）：
    collect_info(sim=None, layout=None, frame=None, profile=None, enemy=None) -> dict
    brief(report, plans, info, cards=None) -> str
    risks(info) -> list[str]

独立 CLI：
    python -m clashlab.prebattle --layout layouts\\th13_sample.json \
        [--profile config\\heroes.json] [--enemy queen=75,king=75,cc=40] \
        --out out\\prebattle
"""
import argparse
import importlib
import json
import os
import sys
import traceback

from . import analysis, defense_findings, planner

# ---------------------------------------------------------------------------
# 并行模块（knowledge / equipment）优雅降级：现在可能还不存在，缺就用空卡 / 空 profile，
# 并在 info["unknown"] 里记录 knowledge_module_missing / equipment_module_missing。
# ---------------------------------------------------------------------------
try:  # pragma: no cover - 取决于并行智能体是否已交付
    from . import knowledge as _knowledge
    _KNOWLEDGE_IMPORT_ERR = None
except Exception as _e:  # noqa: BLE001
    _knowledge = None
    _KNOWLEDGE_IMPORT_ERR = repr(_e)

try:  # pragma: no cover
    from . import equipment as _equipment
    _EQUIPMENT_IMPORT_ERR = None
except Exception as _e:  # noqa: BLE001
    _equipment = None
    _EQUIPMENT_IMPORT_ERR = repr(_e)


# 建筑类型中文名（只做展示用，统计仍以 sim.buildings 的 type 原文为准）
def _cn(type_str):
    try:
        from . import assets
        return assets.STATS.get(type_str, {}).get("cn", type_str)
    except Exception:  # noqa: BLE001
        return type_str


# ---------------------------------------------------------------------------
# 阵型装载：优先复用 cli._sim_from_layout；cli 被并行编辑导致导入失败时本地兜底
# ---------------------------------------------------------------------------
def _load_sim_from_layout(layout, n=44):
    """返回 (sim, data)；优先 cli._sim_from_layout，失败用本地最小装载器。"""
    try:
        from .cli import _sim_from_layout
        return _sim_from_layout(layout, n=n)
    except Exception:  # noqa: BLE001
        from . import assets
        from .sim import Simulator
        with open(layout, "r", encoding="utf-8") as f:
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


def _sim_from_frame(frame, grid_n=44):
    """侦察截图 → 标定 → 建 sim。识别不可靠时返回 (None, note)，绝不硬造。"""
    try:
        from . import vision
    except Exception as e:  # noqa: BLE001
        return None, f"vision_module_unavailable:{e!r}"

    calib, meta = vision.detect_boundary(frame, grid_n=grid_n)
    conf = float(meta.get("confidence", 0.0) or 0.0)
    if calib is None or conf < 0.05:
        return None, f"boundary_low_confidence(source={meta.get('source')},conf={conf:.3f})"
    try:
        dets, _matches, dmeta = vision.scan_layout(frame, calib, thresh=0.5)
        if not dets:
            return None, "frame_buildings_unrecognized"
        sim = vision.buildings_to_sim(dets, n=grid_n)
        return sim, f"frame(source={meta.get('source')},conf={conf:.3f},structures={dmeta.get('structures')},matched={dmeta.get('matched')})"
    except Exception as e:  # noqa: BLE001
        return None, f"frame_sim_build_failed:{e!r}"


# ---------------------------------------------------------------------------
# 敌方已知信息解析：只接受显式传入，绝不猜
# ---------------------------------------------------------------------------
_HERO_KEYS = ("queen", "king", "warden", "rc")


def _parse_enemy(enemy):
    """归一化 enemy：dict 或 None；等级只接受显式数字，其余 None。"""
    out = {"th": None, "queen": None, "king": None, "warden": None,
           "rc": None, "cc": None, "equipment": None}
    if not enemy:
        return out
    if isinstance(enemy, str):
        enemy = _parse_kv_list(enemy)
    if not isinstance(enemy, dict):
        return out
    for k in ("queen", "king", "warden", "rc"):
        v = enemy.get(k)
        out[k] = _to_int(v) if v is not None and str(v) != "" else None
    th = enemy.get("th") or enemy.get("town_hall")
    out["th"] = _to_int(th) if th is not None and str(th) != "" else None
    cc = enemy.get("cc")
    out["cc"] = str(cc) if cc not in (None, "") else None
    eq = enemy.get("equipment")
    out["equipment"] = eq if eq else None
    return out


def _to_int(v):
    try:
        return int(str(v).strip())
    except (ValueError, TypeError):
        return None


def _parse_kv_list(text):
    """queen=75,king=75,cc=40 → dict。"""
    out = {}
    for part in str(text).split(","):
        part = part.strip()
        if not part or "=" not in part:
            continue
        k, v = part.split("=", 1)
        out[k.strip()] = v.strip()
    return out


# ---------------------------------------------------------------------------
# 装备档案（equipment 并行模块）降级读取
# ---------------------------------------------------------------------------
def _load_profile(profile):
    """profile: 路径 str / dict / None。返回 (our_profile, notes, rules)。

    our_profile: {slot: [equipment_id,...]}，对齐契约示例；
    rules: equipment.profile_rules 的输出（无模块/失败为 {}），供 brief 翻译能力。
    """
    notes = []
    if not profile:
        return {}, notes, {}

    prof = None
    rules = {}
    if _equipment is not None:
        try:
            if isinstance(profile, dict):
                prof = profile
            else:
                prof = _equipment.load_profile(str(profile))
            if prof is not None:
                rules = _equipment.profile_rules(prof) or {}
        except Exception as e:  # noqa: BLE001
            notes.append(f"equipment_module_call_failed:{e!r}")
    else:
        # 模块缺失：直接当 JSON 读，再不行空档案
        if isinstance(profile, dict):
            prof = profile
        else:
            try:
                with open(str(profile), "r", encoding="utf-8") as f:
                    prof = json.load(f)
            except Exception as e:  # noqa: BLE001
                notes.append(f"equipment_profile_missing:{os.path.basename(str(profile))}:{e!r}")
                return {}, notes, {}

    # 归一化：优先 equipment 标准外形 {heroes:{slot:{level,equipment:[...]}}}
    out = {}
    heroes = (prof or {}).get("heroes", {}) if isinstance(prof, dict) else {}
    if isinstance(heroes, dict) and heroes:
        for slot, entry in heroes.items():
            if isinstance(entry, dict):
                out[slot] = [str(x) for x in (entry.get("equipment") or [])]
            elif isinstance(entry, list):
                out[slot] = [str(x) for x in entry]
    else:
        out = _normalize_profile(prof)
    return out, notes, rules


def _normalize_profile(prof):
    """兼容旧外形：{hero: [item,...]} / {hero: {equipment:[...]}}。"""
    if not isinstance(prof, dict):
        return {}
    out = {}
    for hero, val in prof.items():
        if isinstance(val, list):
            out[hero] = [str(x) for x in val]
        elif isinstance(val, dict):
            items = val.get("equipment") or val.get("items") or val.get("gear") or []
            out[hero] = [str(x) for x in items]
        else:
            out[hero] = [str(val)]
    return out


# ---------------------------------------------------------------------------
# knowledge 战术卡降级读取
# ---------------------------------------------------------------------------
def _load_cards(info=None, k=3):
    """经 knowledge.retrieve 检索，返回归一化卡片 [{id,title,body,reasons}]。

    无模块 / 无库 / 无命中都返回 []，由 brief 写「无可用战术卡」，绝不编来源。
    """
    if _knowledge is None or not callable(getattr(_knowledge, "retrieve", None)):
        return []
    brief_q = {}
    if info:
        brief_q["th"] = info.get("th") or ""
        brief_q["army"] = ",".join((info.get("our_army") or {}).keys())
        eq = []
        for items in (info.get("our_profile") or {}).values():
            eq += list(items)
        brief_q["equipment"] = ",".join(eq)
        brief_q["keywords"] = ",".join((info.get("defense_counts") or {}).keys())
    try:
        hits = _knowledge.retrieve(brief=brief_q, k=k)
    except TypeError:
        try:
            hits = _knowledge.retrieve(brief_q, k)
        except Exception:  # noqa: BLE001
            return []
    except Exception:  # noqa: BLE001
        return []
    out = []
    for item in hits or []:
        card, reasons = item if isinstance(item, tuple) else (item, [])
        if not isinstance(card, dict):
            continue
        src = card.get("source") or {}
        out.append({
            "id": str(card.get("id") or ""),
            "title": str(card.get("title") or src.get("title") or src.get("name") or ""),
            "body": "；".join(card.get("key_points") or []),
            "reasons": list(reasons or []),
        })
    return [c for c in out if c["id"]]


# ---------------------------------------------------------------------------
# collect_info：字段名固定，勿改
# ---------------------------------------------------------------------------
def collect_info(sim=None, layout=None, frame=None, profile=None, enemy=None) -> dict:
    """归集已知信息。拿不到的字段=null/空，并进 unknown。"""
    enemy = _parse_enemy(enemy)
    unknown = []

    # --- 1. 建 sim：显式 sim > layout 文件 > frame 截图 ---
    sim_note = ""
    if sim is None and layout:
        sim, data = _load_sim_from_layout(layout)
        sim_note = f"layout:{os.path.basename(str(layout))}"
    elif sim is None and frame is not None:
        frame_img = frame
        if isinstance(frame, str):
            from . import vision
            frame_img = vision.imread(frame)
            if frame_img is None:
                unknown.append("frame_unreadable")
        sim, note = _sim_from_frame(frame_img)
        sim_note = note or "frame"
        if sim is None:
            unknown.append(note)
    elif sim is None:
        unknown.append("no_layout_no_frame")

    # --- 2. 防御数量：只从 sim.buildings 实际统计，不凭网格估 ---
    defense_counts = {}
    if sim is not None:
        for b in sim.buildings:
            if float(b.get("dps", 0)) <= 0:
                continue  # 大本营/吹风机等无火力建筑不计入防御数量
            t = b.get("type") or "defense"
            defense_counts[t] = defense_counts.get(t, 0) + 1

    # --- 3. 核心覆盖 / 重心 / 外露 / 盲区：直接取自 defense_report ---
    core_cover_dps = 0
    centroid = []
    exposed = []
    blind = []
    report = None
    if sim is not None and sim.buildings:
        try:
            ring = analysis.deployment_ring(sim, margin=1)
            report = analysis.defense_report(sim, ring, planner.DEFAULT_ARMY)
            core_cover_dps = report.get("core_cover_dps", 0)
            centroid = report.get("centroid", [])
            exposed = [{"type": e["type"], "tile": e["tile"],
                       "dps": e.get("dps"), "edge_dist": e.get("edge_dist")}
                      for e in report.get("exposed", [])]
            blind = [{"tile": b["tile"], "cover": b.get("cover"),
                      "dist_core": b.get("dist_core")}
                     for b in report.get("blind", [])]
        except Exception as e:  # noqa: BLE001
            unknown.append(f"defense_report_failed:{e!r}")

    # --- 4. TH / 敌方英雄 / CC：只接受显式传入，拿不到=null ---
    th = enemy["th"]
    if th is None and layout:
        # layout 文件里显式写了 th 才取，文件没写就不猜
        try:
            with open(layout, "r", encoding="utf-8") as f:
                th = _to_int(json.load(f).get("th"))
        except Exception:  # noqa: BLE001
            th = None

    enemy_hero_levels = {k: enemy[k] for k in _HERO_KEYS}
    enemy_cc = enemy["cc"]

    # --- 5. 我方档案 / 军队 ---
    our_profile, prof_notes, rules = _load_profile(profile)
    our_army = dict(planner.DEFAULT_ARMY.get("troops", {}))

    # --- 6. unknown 清单 ---
    if th is None:
        unknown.append("town_hall_level_unknown")
    if any(v is None for v in enemy_hero_levels.values()):
        unknown.append("enemy_hero_levels_unknown")
    if enemy_cc is None:
        unknown.append("enemy_cc_capacity_unknown")
    unknown.append("enemy_equipment_unknown")
    unknown.append("enemy_cc_troops_unknown")
    unknown.append("trap_positions_unknown")
    if _knowledge is None:
        unknown.append("knowledge_module_missing")
    if _equipment is None:
        unknown.append("equipment_module_missing")
    unknown.extend(prof_notes)
    if sim_note:
        unknown.append(f"source:{sim_note}")

    info = {
        "th": th,
        "layout_id": os.path.basename(str(layout)) if layout else (
            os.path.basename(str(frame)) if isinstance(frame, str) else ""),
        "defense_counts": defense_counts,
        "wall_level": "",
        "core_cover_dps": core_cover_dps,
        "centroid": centroid,
        "exposed": exposed,
        "blind": blind,
        "enemy_hero_levels": enemy_hero_levels,
        "enemy_cc": enemy_cc,
        "our_profile": our_profile,
        "our_army": our_army,
        "unknown": unknown,
    }
    # --- 6.5 布局弱点（大本营偏心 / 对空 / 对地；只取不依赖墙数据的三项）---
    try:
        lay_doc = None
        if layout:
            with open(layout, "r", encoding="utf-8") as f:
                lay_doc = json.load(f)
        _fs = defense_findings.findings(lay_doc)
        if _fs:
            info["defense_findings"] = _fs
            info["defense_summary"] = defense_findings.summary_line(_fs)
    except Exception:  # noqa: BLE001 - 布局缺/坏不阻断简报
        pass

    # 把 report / rules 挂在私有键上供 brief 复用，不进对外契约字段
    info["_report"] = report
    info["_rules"] = rules
    return info


# ---------------------------------------------------------------------------
# risks：规则化生成 3~5 条，不用模型编
# ---------------------------------------------------------------------------
def risks(info) -> list:
    out = []
    dc = info.get("defense_counts") or {}
    heroes = info.get("enemy_hero_levels") or {}
    cc = info.get("enemy_cc")

    # ① 敌方 CC 未知（任何情况都列，容量已知但兵种永远未知）
    if cc is None:
        out.append("未获取敌方 CC 容量与兵种 → 双线/分兵方案存在援军反打风险，若敌方 CC 是雷龙，分兵会被单点反打。")
    else:
        out.append(f"敌方 CC 容量 {cc} 已记录，但兵种未获取 → 若 CC 内是雷龙/超法，双线会被援军反打，需留一发毒药。")

    # ② 敌方英雄等级/装备未知
    if any(v is None for v in (heroes.get("queen"), heroes.get("king"),
                               heroes.get("warden"), heroes.get("rc"))):
        out.append("未获取敌方英雄等级与装备 → 对位斩杀线、技能爆发窗口未建模，女王/咏王可能提前开技能反打。")
    else:
        out.append("敌方英雄等级已传入，装备仍未获取 → 装备克制（如巨型箭头/无敌法术瓶）未建模。")

    # ③ 防空均布 → 单点切入交叉覆盖
    ad = dc.get("air-defense", 0)
    if ad >= 4:
        out.append(f"防空 {ad} 座均布 → 单点切入会被交叉覆盖，空军队形必须先定点拆防空再压核心。")
    elif ad > 0:
        out.append(f"防空仅 {ad} 座 → 空军队形可走，但漏拆任一防空都会导致龙群被集火。")

    # ③.5 布局弱点（大本营偏心 / 对空 / 对地；数据干净、不依赖墙线）
    for _f in (info.get("defense_findings") or [])[:2]:
        _txt = str(_f.get("text", "")).strip()
        if _txt:
            out.append("布局弱点：" + _txt)

    # ④ 散射炮 / 地狱塔 / 鹰火炮 具体威胁
    if dc.get("scattershot", 0) > 0:
        out.append(f"散射炮 {dc['scattershot']} 座 → 龙群集群走位吃溅射，需分散落点或先手拔除。")
    if dc.get("inferno-tower", 0) > 0:
        out.append(f"地狱塔 {dc['inferno-tower']} 座 → 持续灼烧对高血量单位威胁大，需冰冻或爆发秒掉。")
    if dc.get("eagle-artillery", 0) > 0:
        out.append(f"鹰火炮 {dc['eagle-artillery']} 座 → 远程压制集结期大部队，推进需在其开火窗口前减员。")

    # ⑤ 战术卡库缺失兜底
    if "knowledge_module_missing" in (info.get("unknown") or []):
        out.append("战术卡库（knowledge）缺失 → 推荐打法仅为规则引擎输出，未经历史案例校验。")

    # 无阵型兜底
    if not dc:
        out.append("未获得可计算阵型 → 防御数量/覆盖/重心全部缺失，本简报只列已知项，待补侦察。")

    # 去重并封顶 5 条，保底 3 条
    seen, uniq = set(), []
    for r in out:
        key = r[:18]
        if key not in seen:
            seen.add(key)
            uniq.append(r)
    uniq = uniq[:5]
    while len(uniq) < 3:
        uniq.append("信息不足：该条目为兜底风险，侦察补齐后重跑本简报。")
    return uniq


# ---------------------------------------------------------------------------
# brief：固定五段，≤900 字
# ---------------------------------------------------------------------------
def _strip_end(s):
    return str(s).rstrip("。！？；;，, ")


def _compose_brief(report, plans, info, cards, level=2) -> str:
    """level: 2=全量(装备能力长句+卡标题) 1=去能力长句 0=卡片只留 id。"""
    dc = info.get("defense_counts") or {}
    th = info.get("th")
    th_txt = f"TH{th}" if th else "TH 等级未获取"
    dc_txt = "，".join(f"{_cn(k)}×{v}" for k, v in dc.items()) or "未统计到防御（无阵型来源）"

    # 重心方位
    cent = info.get("centroid") or []
    if len(cent) == 2:
        qx = "右" if cent[0] > 22.5 else ("左" if cent[0] < 21.5 else "中")
        qy = "下" if cent[1] > 22.5 else ("上" if cent[1] < 21.5 else "中")
        grav = f"({cent[0]},{cent[1]})，{qx}{qy}偏重"
    else:
        grav = "未算出"

    # ① 对手骨架
    sec1 = (f"【①对手骨架】{th_txt}；防御：{dc_txt}。"
            f"核心 7x7 覆盖 {info.get('core_cover_dps', 0)} dps，"
            f"防御重心 {grav}。")

    # ② 三个必须先拆的点（用 defense_report 的 priority 字段）
    pri = (report or {}).get("priority", []) or []
    lines = []
    for p in pri[:3]:
        lines.append(f"{_cn(p['type'])}({p['tile'][0]},{p['tile'][1]})，"
                      f"外露 {p['edge_dist']} 格，优先级 {p['priority']}")
    if not lines:
        for e in (info.get("exposed") or [])[:3]:
            lines.append(f"{_cn(e['type'])}({e['tile'][0]},{e['tile'][1]})，距撒兵环 {e.get('edge_dist')} 格")
    if not lines:
        lines.append("无可用优先级数据（阵型未识别）")
    sec2 = "【②必须先拆的三点】" + "；".join(lines) + "。"

    # ③ 我方可用能力（装备→能力，缺什么写缺什么）
    prof = info.get("our_profile") or {}
    rules = info.get("_rules") or {}
    if prof:
        worn = "；".join(f"{h} 穿 {', '.join(items)}" for h, items in prof.items() if items)
        if level >= 2:
            enabled = set(rules.get("enabled") or [])
            extra = []
            for eid, r in (rules.get("rules") or {}).items():
                if eid in enabled and r.get("effect"):
                    extra.append(f"{eid}→{r['effect']}")
            cap = worn + ("；能力：" + "；".join(extra[:2]) if extra else "")
        else:
            cap = worn
    else:
        cap = "未加载英雄装备档案（未传 --profile），可用能力按默认雷龙平推估计，具体装备加成未知"
    army = info.get("our_army") or {}
    army_txt = "，".join(f"{k}×{v}" for k, v in army.items() if v) or "默认编队"
    sec3 = f"【③我方可用能力】编队 {army_txt}；装备：{cap}。"

    # ④ 推荐打法（引用 knowledge 卡 id；无卡明说，不许编来源）
    if cards:
        cite = "，".join(f"[{c['id']}]" for c in cards[:3])
        if level >= 1:
            card_txt = "参考战术卡 " + cite + "：" + "；".join(
                f"[{c['id']}] {c['title'] or c['id']}" for c in cards[:3])
        else:
            card_txt = "参考战术卡 " + cite
    else:
        card_txt = "无可用战术卡，按规则引擎输出"
    top = (plans or [None])[0]
    if top:
        plan_txt = (f"规则引擎首选 {top['id']}「{top['name']}」"
                    f"（相对预测 {top.get('predicted')}，风险 {top.get('risk')}）："
                    f"{_strip_end(top.get('rationale', ''))}")
    else:
        plan_txt = "规则引擎未产出候选方案（无阵型数据）"
    sec4 = f"【④推荐打法】{card_txt}。{plan_txt}。"

    # ⑤ 三个失效风险
    rk = risks(info)
    sec5 = "【⑤失效风险】" + "；".join(
        f"{i+1}) {_strip_end(r)}" for i, r in enumerate(rk[:3])) + "。"

    return "\n".join([sec1, sec2, sec3, sec4, sec5])


def brief(report, plans, info, cards=None) -> str:
    cards = cards if cards is not None else _load_cards(info)
    # 分级压缩：全量 → 去能力长句 → 卡片只留 id，保证 ≤900 字
    text = _compose_brief(report, plans, info, cards, level=2)
    if len(text) > 900:
        text = _compose_brief(report, plans, info, cards, level=1)
    if len(text) > 900:
        text = _compose_brief(report, plans, info, cards, level=0)
    return text


# ---------------------------------------------------------------------------
# 独立 CLI（不走 cli.py）
# ---------------------------------------------------------------------------
def _write_json(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def run_cli(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="clashlab.prebattle",
                                 description="赛前简报：阵型/侦察/已知信息 → info.json + brief.md")
    ap.add_argument("--layout", default="", help="阵型 JSON（优先于 --frame）")
    ap.add_argument("--frame", default="", help="侦察截图 PNG/JPG（无 layout 时用）")
    ap.add_argument("--profile", default="", help="我方英雄装备档案 JSON（config/heroes.json）")
    ap.add_argument("--enemy", default="", help="显式已知敌方信息，如 queen=75,king=75,warden=50,rc=30,cc=40,th=13")
    ap.add_argument("--out", default="out/prebattle", help="输出目录，默认 out/prebattle")
    ap.add_argument("--grid", type=int, default=44)
    args = ap.parse_args(argv)

    os.makedirs(args.out, exist_ok=True)
    enemy = _parse_kv_list(args.enemy) if args.enemy else None

    info = collect_info(sim=None, layout=args.layout or None,
                         frame=args.frame or None,
                         profile=args.profile or None, enemy=enemy)

    # report / plans 供 brief 使用（info 内已存 report，这里复用或重算）
    report = info.get("_report")
    plans = []
    sim = None
    if info.get("defense_counts") or report is not None:
        # 重新建一次 sim 拿 plans（collect_info 没保留 sim）
        if args.layout:
            sim, _ = _load_sim_from_layout(args.layout, n=args.grid)
        elif args.frame:
            from . import vision
            frame_img = vision.imread(args.frame)
            sim, _note = _sim_from_frame(frame_img, grid_n=args.grid)
    if sim is not None and sim.buildings:
        if report is None:
            ring = analysis.deployment_ring(sim, margin=1)
            report = analysis.defense_report(sim, ring, planner.DEFAULT_ARMY)
        plans = analysis.candidate_plans(sim, analysis.deployment_ring(sim, margin=1),
                                          planner.DEFAULT_ARMY, report=report, topk=3)

    cards = _load_cards(info)
    text = brief(report, plans, info, cards=cards)

    # 落盘：info.json（剔除私有键）+ brief.md + 日志
    info_out = {k: v for k, v in info.items() if not k.startswith("_")}
    _write_json(info_out, os.path.join(args.out, "info.json"))
    with open(os.path.join(args.out, "brief.md"), "w", encoding="utf-8") as f:
        f.write(text + "\n")

    log = {
        "layout": args.layout, "frame": args.frame, "profile": args.profile,
        "enemy_raw": args.enemy,
        "cards_loaded": len(cards),
        "brief_chars": len(text),
        "risk_count": len(risks(info)),
        "knowledge_module": _knowledge is not None,
        "equipment_module": _equipment is not None,
    }
    _write_json(log, os.path.join(args.out, "run.log.json"))

    # 控制台：brief 前 5 行 + risks
    lines = text.splitlines()
    print("=== brief（前 5 行）===")
    for ln in lines[:5]:
        print(ln)
    print(f"\n[brief 字数] {len(text)} / 900")
    print("=== risks ===")
    for i, r in enumerate(risks(info), 1):
        print(f"{i}. {r}")
    return 0


def main(argv=None):
    try:
        return run_cli(argv)
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
