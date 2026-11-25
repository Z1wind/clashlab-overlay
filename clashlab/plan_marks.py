# -*- coding: utf-8 -*-
"""屏幕绘制标注层（marks）：把规则方案落成 UI 可直接画的 draw_calls JSON。

设计：
1. 规则算法（giant_arrow / hero_spots / troop_drop / build_marks）不依赖任何大模型，
   模型不可用时依然完整产出（source=rule）。
2. 模型只在规则草案之上给「变更补丁」，validate_marks 软失败丢弃非法条目，
   merge_marks 合并，冲突时以「坐标在环内 + 穿防空数不降低」为准。
3. 坐标统一 44×44 整数格号；像素换算由 UI 用 Calib.tile_to_px 完成。

本模块可独立运行：
    python -m clashlab.plan_marks marks --layout layouts\\th13_sample.json --style terse --out out\\marks
同时导出 cmd_marks(args) 供 cli.py 一行接线（cli 侧由经理统一改）。
"""
import argparse
import copy
import json
import math
import os
import sys
import time

import numpy as np

from . import analysis, assets, planner, prompts

GRID_N = 44
ARROW_MAX_LEN = 30          # 穿云箭射线长度上限（格）
ARROW_HIT_TOL = 1.2         # 垂直偏差命中容差（格）
ARROW_DIRS = 16
ARROW_MAX_DIST = 32         # validate：from→to 直线距离上限
HOT_Q = 0.90                # 环上 dps 前 10% 视为高热区，英雄避开

HERO_ROLES = ("queen", "king", "warden", "rc")
TROOP_ROLES = ("edrag",)
ALL_PIN_ROLES = HERO_ROLES + TROOP_ROLES + ("freeze",)


# ---------------- 工具 ----------------

def _ring_set(ring):
    xs, ys = np.where(ring.astype(bool))
    return set(zip(xs.tolist(), ys.tolist()))


def _ring_cells(ring):
    xs, ys = np.where(ring.astype(bool))
    return list(zip(xs.tolist(), ys.tolist()))


def _cn(btype):
    return assets.STATS.get(btype, {}).get("cn", btype)


def _valid_tile(t):
    return (isinstance(t, (list, tuple)) and len(t) == 2
            and all(isinstance(v, (int, float)) for v in t)
            and 1 <= int(round(t[0])) <= GRID_N - 1
            and 1 <= int(round(t[1])) <= GRID_N - 1)


def _snap_to_ring(tile, ring, rset):
    """硬校验：tile 在环内原样返回；否则退到最近合法环格，返回 (tile, 偏移格数)。

    不用距离近似判断，直接做环集合成员检查；被封锁的最优站位自动偏移并在 note 记录。
    """
    key = (int(round(tile[0])), int(round(tile[1])))
    if key in rset:
        return [key[0], key[1]], 0
    best = None
    for (x, y) in _ring_cells(ring):
        d = abs(x - key[0]) + abs(y - key[1])
        if best is None or d < best[0]:
            best = (d, [x, y])
    return best[1], best[0]


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _ray_hits(sim, fr, to):
    """沿 from→to 线段统计命中的防空建筑（垂直偏差 ≤1.2，投影在线段上）。"""
    fx, fy = fr[0], fr[1]
    tx, ty = to[0], to[1]
    vx, vy = tx - fx, ty - fy
    vlen = math.hypot(vx, vy)
    hits = []
    if vlen < 1e-6:
        return hits
    dx, dy = vx / vlen, vy / vlen
    for b in sim.buildings:
        if b["type"] != "air-defense":
            continue
        ax, ay = b["tile"]
        wx, wy = ax - fx, ay - fy
        proj = wx * dx + wy * dy
        if proj < 0 or proj > vlen:
            continue
        perp = abs(wx * dy - wy * dx)
        if perp <= ARROW_HIT_TOL:
            hits.append([int(ax), int(ay)])
    return hits


# ---------------- 规则 1：女王穿云箭 ----------------

def giant_arrow(sim, ring, army, entry=None):
    """枚举环上候选站位 × 16 方向，选命中防空最多、最安全、最贴主攻的一条射线。

    entry: 主攻入点 [x,y]（可选），用于射线与主攻背向夹角惩罚。
    返回 {"from", "to", "hits", "score", "note"}；命中 0 时也给最佳方向，note 写明未穿防空。
    """
    ads = [b["tile"] for b in sim.buildings if b["type"] == "air-defense"]
    cells = _ring_cells(ring)

    best = None
    for (x, y) in cells:
        # 筛：到最近防空 ≤30 格（欧氏），过远的站位射线根本够不着
        if ads and min(math.hypot(x - a[0], y - a[1]) for a in ads) > ARROW_MAX_LEN:
            continue
        for k in range(ARROW_DIRS):
            ang = 2 * math.pi * k / ARROW_DIRS
            dx, dy = math.cos(ang), math.sin(ang)
            hits = []
            for ax, ay in ads:
                wx, wy = ax - x, ay - y
                proj = wx * dx + wy * dy
                if proj < 0 or proj > ARROW_MAX_LEN:
                    continue
                perp = abs(wx * dy - wy * dx)
                if perp <= ARROW_HIT_TOL:
                    hits.append([int(ax), int(ay)])
            # 打分：命中×10 - 站位当前受击 dps 惩罚 - 与主攻方向夹角过大惩罚
            score = len(hits) * 10.0 - float(sim.dps[x, y]) / 100.0
            if entry is not None:
                vx, vy = entry[0] - x, entry[1] - y
                elen = math.hypot(vx, vy)
                if elen > 1e-6:
                    cos = (vx * dx + vy * dy) / elen
                    if cos < -0.1:  # 射线与主攻背向，扣分
                        score -= 2.0
            if best is None or score > best[0]:
                best = (score, (x, y), (dx, dy), hits)

    if best is None:
        return {"from": [GRID_N // 2, 2], "to": [GRID_N // 2, GRID_N - 2],
                "hits": [], "score": -99.0, "note": "环上无候选站位，给默认方向"}

    score, (x, y), (dx, dy), hits = best
    tx = int(round(x + dx * ARROW_MAX_LEN))
    ty = int(round(y + dy * ARROW_MAX_LEN))
    tx = max(1, min(GRID_N - 1, tx))
    ty = max(1, min(GRID_N - 1, ty))
    note = (f"穿过 {len(hits)} 座防空" if hits else "未穿过防空，给最佳方向占位")
    return {"from": [int(x), int(y)], "to": [tx, ty], "hits": hits,
            "score": round(score, 2), "note": note}


# ---------------- 规则 2：英雄站位 ----------------

def _hot_mask(ring, sim):
    vals = sim.dps[ring.astype(bool)]
    vals = vals[vals > 0]
    if len(vals) == 0:
        return np.zeros_like(ring)
    thresh = float(np.quantile(vals, HOT_Q))
    return ring & (sim.dps >= thresh)


def _nearest_safe(ring, hot, anchor):
    """环上离 anchor 最近的非高热格；全热时退化为最近环格。"""
    safe = _ring_cells(ring & ~hot) or _ring_cells(ring)
    return min(safe, key=lambda c: abs(c[0] - anchor[0]) + abs(c[1] - anchor[1]))


def hero_spots(sim, ring, report, plans, arrow):
    """女王=穿云箭站位（与主攻入点冲突则退后2格）；蛮王顶前；守护者殿后；冠军走另一侧。

    每点都落在环内且避开 dps 前 10% 的高热格。返回 pins 列表（不含 order/label，由上层补）。
    """
    center = report.get("centroid") or [sim.n / 2, sim.n / 2]
    cx, cy = center[0], center[1]
    entry = plans[0]["entries"][0]["tile"] if plans and plans[0].get("entries") else [cx, cy]
    hot = _hot_mask(ring, sim)

    out = []

    # 女王：默认穿云箭站位；与主攻入点贴太近（切比雪夫 ≤1）则保留入点，女王退后 2 格
    af = arrow["from"]
    if abs(af[0] - entry[0]) <= 1 and abs(af[1] - entry[1]) <= 1:
        back = [int(entry[0] + 2 * math.copysign(1, entry[0] - cx or 1)),
                int(entry[1] + 2 * math.copysign(1, entry[1] - cy or 1))]
        queen = _nearest_safe(ring, hot, back)
        q_note = "与主攻入点冲突，退后2格"
    else:
        queen = tuple(af)
        q_note = "穿云箭站位"
    out.append({"kind": "hero", "role": "queen", "tile": [int(queen[0]), int(queen[1])],
                "label": "女王站位", "note": q_note})

    # 蛮王：入点前 1~2 格朝防御方向（承接火力）
    king_anchor = [int(entry[0] + (cx - entry[0]) * 0.4),
                   int(entry[1] + (cy - entry[1]) * 0.4)]
    king = _nearest_safe(ring, hot, king_anchor)
    out.append({"kind": "hero", "role": "king", "tile": [int(king[0]), int(king[1])],
                "label": "蛮王顶前", "note": "入点前1-2格承接火力"})

    # 大守护者：主攻后方 3 格殿后
    warden_anchor = [int(entry[0] + 3 * math.copysign(1, entry[0] - cx or 1)),
                     int(entry[1] + 3 * math.copysign(1, entry[1] - cy or 1))]
    warden = _nearest_safe(ring, hot, warden_anchor)
    out.append({"kind": "hero", "role": "warden", "tile": [int(warden[0]), int(warden[1])],
                "label": "大守护者殿后", "note": "主攻后方3格"})

    # 冠军：走另一侧，挑 report.exposed 最外露目标对面的环格
    exposed = report.get("exposed") or []
    rc_anchor = [int(2 * cx - entry[0]), int(2 * cy - entry[1])]
    rc = _nearest_safe(ring, hot, rc_anchor)
    exp_label = _cn(exposed[0]["type"]) if exposed else "外露防御"
    out.append({"kind": "hero", "role": "rc", "tile": [int(rc[0]), int(rc[1])],
                "label": "冠军牵制", "note": f"另一侧牵制{exp_label}"})
    return out


# ---------------- 规则 3：雷龙分批投放 ----------------

def troop_drop(plans, arrow):
    """最佳方案首入点的雷龙分 2 批同点下放，间隔约 1.5s。返回 (pins, best_plan)。"""
    pins = []
    if not plans or not plans[0].get("entries"):
        return pins, None
    best = plans[0]
    entry = best["entries"][0]
    total = int(entry.get("troops", 7))
    n1 = max(1, total // 2)
    n2 = max(1, total - n1)
    tx, ty = int(entry["tile"][0]), int(entry["tile"][1])
    pins.append({"kind": "troop", "role": "edrag", "tile": [tx, ty], "count": n1,
                 "label": f"雷龙第1批×{n1}", "note": "先手下，间隔约1.5s"})
    pins.append({"kind": "troop", "role": "edrag", "tile": [tx, ty], "count": n2,
                 "label": f"雷龙第2批×{n2}", "note": "同入点1.5s后跟进"})
    return pins, best


# ---------------- 规则 4：合成 draw_calls ----------------

def build_marks(sim, ring, report, plans, army, profile=None, cards=None, prebattle=None):
    """合成完整 draw_calls：先拆目标/避开标注 + 穿云箭线 + 英雄/部队 pins + 步骤。

    profile: 原始英雄装备画像 dict（equipment.load_profile 产物）；None 时保持旧行为
    （默认允许穿云箭）。giant-arrow 未穿戴则不画射线，女王改跟队切入。
    cards: [(card, reason)] 检索命中的战术卡；顶层记录 ids，steps 首条引用首张卡。
    prebattle: 赛前简报文本（仅记录 meta，不编造）。
    """
    from . import equipment
    rules = equipment.profile_rules(profile) if isinstance(profile, dict) else None

    def _allowed(eid):
        return rules is None or bool(rules["rules"].get(eid, {}).get("allowed", True))

    ga_on = _allowed("giant-arrow")
    entry0 = plans[0]["entries"][0]["tile"] if plans and plans[0].get("entries") else None
    rset = _ring_set(ring)

    if ga_on:
        arrow = giant_arrow(sim, ring, army, entry=entry0)
        # 硬校验：穿云箭站位必须真在环内，被封锁则退最近合法环格并记录偏移
        arrow["from"], off = _snap_to_ring(arrow["from"], ring, rset)
        if off:
            arrow["note"] += f"；站位被封锁，偏移{off}格至{arrow['from']}"
    else:
        # 未穿戴巨型箭：不给射线，女王跟队切入（占位 from 供 hero_spots 取位）
        arrow = {"from": list(entry0) if entry0 else [22, 2], "to": None,
                 "hits": [], "score": 0.0, "note": "未穿戴巨型箭，不画穿云箭"}

    heroes = hero_spots(sim, ring, report, plans, arrow)
    drops, best_plan = troop_drop(plans, arrow)

    # earthquake-boots 允许：入点前移 1~2 格（朝中心），缩短地面推进
    if _allowed("earthquake-boots") and best_plan and report.get("centroid"):
        cx, cy = report["centroid"]
        for p in drops:
            dx, dy = cx - p["tile"][0], cy - p["tile"][1]
            step = 1 if abs(dx) + abs(dy) > 4 else 2
            nx = p["tile"][0] + (1 if dx > 0 else -1 if dx < 0 else 0) * step
            ny = p["tile"][1] + (1 if dy > 0 else -1 if dy < 0 else 0) * step
            t, off = _snap_to_ring([nx, ny], ring, rset)
            p["tile"] = t
            p["note"] = p.get("note", "") + "；地震靴入点前移" + (f"{off}格" if off else "1-2格")

    # 所有 pin 硬校验落环，被封锁则偏移并在 note 写明
    for p in heroes + drops:
        t, off = _snap_to_ring(p["tile"], ring, rset)
        p["tile"] = t
        if off:
            p["note"] = p.get("note", "") + f"；原站位被封锁，偏移{off}格"

    # 未穿巨型箭：女王改跟队切入，贴雷龙入点侧后方
    if not ga_on:
        queen = next((p for p in heroes if p["role"] == "queen"), None)
        if queen and entry0:
            qt, _off = _snap_to_ring(entry0, ring, rset)
            queen["tile"] = qt
            queen["label"] = "女王跟队切入"
            queen["note"] = "未穿戴巨型箭，不画穿云箭，女王跟队雷龙波次切入"

    marks = []
    seq = 1
    seen = set()

    # 先拆目标：report.priority（字段 type/tile/value/edge_dist/priority）前 3 个
    for p in (report.get("priority") or [])[:3]:
        key = tuple(p["tile"])
        if key in seen:
            continue
        seen.add(key)
        marks.append({"kind": "building", "tile": [int(p["tile"][0]), int(p["tile"][1])],
                      "label": _cn(p["type"]), "role": "target", "seq": seq})
        seq += 1
    # 穿云箭命中的防空标 snipe
    for h in arrow["hits"]:
        key = tuple(h)
        if key in seen:
            continue
        seen.add(key)
        marks.append({"kind": "building", "tile": [int(h[0]), int(h[1])],
                      "label": "防空", "role": "snipe", "seq": seq})
        seq += 1
    # 避开：dps 最高的 1~2 座（不在先拆清单里）
    for b in sorted((b for b in sim.buildings if b["dps"] > 0),
                    key=lambda b: -b["dps"])[:2]:
        key = tuple(b["tile"])
        if key in seen:
            continue
        seen.add(key)
        marks.append({"kind": "building", "tile": [int(b["tile"][0]), int(b["tile"][1])],
                      "label": _cn(b["type"]), "role": "avoid", "seq": seq})
        seq += 1

    lines = []
    if ga_on:
        lines.append({"kind": "giant_arrow", "from": arrow["from"], "to": arrow["to"],
                      "hits": arrow["hits"],
                      "label": f"穿云箭 穿过{len(arrow['hits'])}座防空"})

    pins = heroes + drops
    for i, p in enumerate(pins, 1):
        p["order"] = i

    # 法术圈：把最高 dps 的先拆/避开目标罩一个冰冻圈
    circles = []
    avoid = [m for m in marks if m["role"] == "avoid"]
    if avoid:
        circles.append({"kind": "freeze", "tile": avoid[0]["tile"], "radius": 4})

    entry = best_plan["entries"][0]["tile"] if best_plan else None
    steps = []

    def _pt(t):
        return f"({t[0]},{t[1]})"

    # 卡片引用：首张命中卡 id 挂首条动作（只引用真实存在的卡）
    card_ids = []
    for item in (cards or []):
        c = item[0] if isinstance(item, tuple) else item
        if c.get("id"):
            card_ids.append(c["id"])
    cite = f" [{card_ids[0]}]" if card_ids else ""

    if entry:
        b1 = next((p for p in drops if p["label"].startswith("雷龙第1批")), None)
        b2 = next((p for p in drops if p["label"].startswith("雷龙第2批")), None)
        n1 = b1["count"] if b1 else "?"
        n2 = b2["count"] if b2 else "?"
        drop_tile = b1["tile"] if b1 else entry
        if ga_on:
            steps.append(f"女王 {_pt(arrow['from'])} 朝 {_pt(arrow['to'])} 放穿云箭，"
                         f"{arrow['note']}{cite}")
        else:
            steps.append(f"女王 {_pt(next(p for p in heroes if p['role']=='queen')['tile'])} "
                         f"跟队雷龙波次切入，未穿戴巨型箭不画射线{cite}")
        steps.append(f"雷龙第1批×{n1} 从 {_pt(drop_tile)} 下，约1.5s后第2批×{n2} 同点跟进")

    king = next((p for p in heroes if p["role"] == "king"), None)
    warden = next((p for p in heroes if p["role"] == "warden"), None)
    rc = next((p for p in heroes if p["role"] == "rc"), None)

    # 装备能力体现在 steps（按 allowed 开关，未穿戴不写其技能）
    king_tail = ""
    if _allowed("spiky-ball"):
        king_tail += "，尖刺球滚清密集防御群"
    if king and warden:
        warden_tail = "殿后3格"
        if _allowed("eternal-tome"):
            warden_tail += "，开书群体无敌扛爆发"
        elif rules is not None and not rules["rules"].get("eternal-tome", {}).get("allowed", True):
            warden_tail += "，无永恒之书不硬扛爆发"
        if _allowed("healing-tome"):
            warden_tail += "，中段开治疗书抬血"
        steps.append(f"蛮王 {_pt(king['tile'])} 顶前承接火力{king_tail}，"
                     f"守护者 {_pt(warden['tile'])} {warden_tail}")
    if rc:
        rc_tail = "走另一侧牵制"
        if _allowed("seeking-shield"):
            rc_tail += "，掷盾弹射处理侧翼防空"
        if _allowed("hog-rider-puppet"):
            rc_tail += "，野猪木偶跳墙侧翼切入"
        steps.append(f"冠军 {_pt(rc['tile'])} {rc_tail}")

    # 隐身药水时机
    if _allowed("invisibility-vial"):
        steps.append("女王进内圈前开隐身药水规避火力，打完显形后撤")
    elif rules is not None and not rules["rules"].get("invisibility-vial", {}).get("allowed", True):
        if _allowed("eternal-tome"):
            steps.append("无隐身药水，女王不单独前探，改由守护者开书抗爆发")

    targets = [f"{m['label']}{_pt(m['tile'])}" for m in marks if m["role"] in ("target", "snipe")][:2]
    if targets:
        steps.append("先拆 " + "、".join(targets) + "，压核心")
    if avoid:
        steps.append(f"避开 {avoid[0]['label']}{_pt(avoid[0]['tile'])} 高dps，必要时冰冻")

    # prebattle 未知项约束（只列 info.unknown 里真实存在的条目，不假设）
    pb_unknown = (prebattle or {}).get("unknown") if isinstance(prebattle, dict) else []
    unknown_steps = []
    if "enemy_cc_troops_unknown" in pb_unknown:
        unknown_steps.append("敌方 CC 兵种未知，留一发毒药应对援军")
    if "trap_positions_unknown" in pb_unknown:
        unknown_steps.append("陷阱位置未知，主力避开边缘零散格")
    if "enemy_equipment_unknown" in pb_unknown:
        unknown_steps.append("敌方英雄装备未知，不假设其技能窗口")
    # 开局/投放两条之后优先插入未知约束，再排通用步骤，最后截 6 条
    head, tail = steps[:2], steps[2:]
    steps = head + unknown_steps + tail
    steps = steps[:6]

    out = {"version": 1, "marks": marks, "lines": lines,
           "pins": pins, "circles": circles, "steps": steps,
           "source": "rule", "arrow_note": arrow["note"]}
    if rules is not None:
        out["profile"] = {"used": rules["enabled"], "missing": rules["missing"]}
    if card_ids:
        out["cards"] = card_ids
    if isinstance(prebattle, dict):
        out["prebattle"] = {
            "th": prebattle.get("th"),
            "unknown": list(prebattle.get("unknown") or []),
            "brief_chars": prebattle.get("brief_chars", 0),
        }
    return out


# ---------------- 校验（软失败） ----------------

def validate_marks(obj, ring, sim):
    """校验模型补丁：坐标 1..43、from 在环内、from→to ≤32、pins.tile 在环内、steps ≤6 条 ≤40字。

    非法条目软失败丢弃并保留规则结果；返回 (clean_patch, issues)。
    """
    issues = []
    clean = {}
    if not isinstance(obj, dict):
        return clean, ["[soft] 补丁不是 JSON 对象，整份保留规则结果"]
    rset = _ring_set(ring)

    ga = obj.get("giant_arrow")
    if isinstance(ga, dict):
        fr, to = ga.get("from"), ga.get("to")
        if (_valid_tile(fr) and _valid_tile(to)
                and (int(fr[0]), int(fr[1])) in rset
                and _dist(fr, to) <= ARROW_MAX_DIST):
            clean["giant_arrow"] = {"from": [int(fr[0]), int(fr[1])],
                                    "to": [int(to[0]), int(to[1])],
                                    "reason": str(ga.get("reason", ""))[:25]}
        else:
            issues.append(f"[soft] giant_arrow 非法 {fr}->{to}，保留规则草案")

    out_pins = []
    for p in (obj.get("pins") or [])[:8]:
        if not isinstance(p, dict):
            continue
        role = str(p.get("role", ""))
        tile = p.get("tile")
        if role not in ALL_PIN_ROLES:
            issues.append(f"[soft] pins 未知 role {role}，跳过该条")
            continue
        if not _valid_tile(tile) or (int(tile[0]), int(tile[1])) not in rset:
            issues.append(f"[soft] pins {role} 非法/不在环 {tile}，跳过该条")
            continue
        out_pins.append({"role": role, "tile": [int(round(tile[0])), int(round(tile[1]))]})
    if out_pins:
        clean["pins"] = out_pins

    steps = []
    for s in (obj.get("steps") or [])[:6]:
        s = str(s).strip()
        if s:
            steps.append(s[:40])
    if steps:
        clean["steps"] = steps

    if not clean:
        issues.append("[soft] 补丁清洗后无可用字段，整份保留规则结果")
    return clean, issues


# ---------------- 合并 ----------------

def merge_marks(rule_calls, patch, ring=None, sim=None):
    """补丁覆盖规则输出；冲突时以「坐标在环内 + 命中数不降低」为优先。

    返回 (merged, applied[])。applied 非空时顶层 source=merged。
    """
    out = copy.deepcopy(rule_calls)
    applied = []
    patch = patch or {}
    rset = _ring_set(ring) if ring is not None else None

    ga = patch.get("giant_arrow")
    if ga and out.get("lines"):
        rule_hits = len(out["lines"][0].get("hits", []))
        hits = _ray_hits(sim, ga["from"], ga["to"]) if sim is not None else out["lines"][0].get("hits", [])
        if len(hits) >= rule_hits:
            line = dict(out["lines"][0])
            frm = [int(ga["from"][0]), int(ga["from"][1])]
            if rset is not None:
                frm, _off = _snap_to_ring(frm, ring, rset)
            line["from"] = frm
            line["to"] = [int(ga["to"][0]), int(ga["to"][1])]
            line["hits"] = hits
            if ga.get("reason"):
                line["reason"] = str(ga["reason"])[:25]
            out["lines"][0] = line
            applied.append("giant_arrow")
        else:
            applied.append("giant_arrow_rejected:hit_drop")

    rule_idx = {p.get("role"): i for i, p in enumerate(out.get("pins", []))}
    for p in patch.get("pins", []):
        role = p.get("role")
        if role in rule_idx:
            tile = [int(p["tile"][0]), int(p["tile"][1])]
            if rset is not None:
                tile, _off = _snap_to_ring(tile, ring, rset)
            out["pins"][rule_idx[role]]["tile"] = tile
            applied.append(f"pin:{role}")

    if patch.get("steps"):
        out["steps"] = patch["steps"]
        applied.append("steps")

    real = [a for a in applied if not a.endswith("_rejected:hit_drop")]
    out["source"] = "merged" if real else rule_calls.get("source", "rule")
    return out, applied


# ---------------- 坐标合法性自检 ----------------

def coord_audit(calls, ring):
    """统计每个 pin/mark/line 端点是否合法（from/pins 必须在环内；mark 是建筑不要求在环）。"""
    rset = _ring_set(ring)
    stats = {"pins_total": 0, "pins_in_ring": 0, "lines_total": 0,
             "lines_from_in_ring": 0, "lines_to_bounds": 0, "marks_total": 0,
             "issues": []}
    for p in calls.get("pins", []):
        stats["pins_total"] += 1
        t = tuple(p["tile"])
        if t in rset:
            stats["pins_in_ring"] += 1
        else:
            stats["issues"].append(f"pin {p.get('role')} {t} 不在环内")
    for ln in calls.get("lines", []):
        stats["lines_total"] += 1
        if tuple(ln["from"]) in rset:
            stats["lines_from_in_ring"] += 1
        else:
            stats["issues"].append(f"line from {ln['from']} 不在环内")
        if _valid_tile(ln["to"]):
            stats["lines_to_bounds"] += 1
        else:
            stats["issues"].append(f"line to {ln['to']} 越界")
    stats["marks_total"] = len(calls.get("marks", []))
    return stats


# ---------------- 业务封装 ----------------

def _load_sim(layout, grid=44):
    from .cli import _sim_from_layout  # 懒导入，避免模块级拉起 cli 重依赖
    return _sim_from_layout(layout, n=grid)


def _load_prebattle(info_path):
    """读 prebattle info.json；附 brief.md 字数；失败返回 None（不阻塞出图）。"""
    if not info_path or not os.path.exists(info_path):
        return None
    try:
        with open(info_path, "r", encoding="utf-8") as f:
            info = json.load(f)
    except Exception as e:
        return {"_load_error": str(e)[:120]}
    brief_path = os.path.join(os.path.dirname(info_path), "brief.md")
    chars = 0
    brief_text = ""
    if os.path.exists(brief_path):
        try:
            with open(brief_path, "r", encoding="utf-8") as f:
                brief_text = f.read()
            chars = len(brief_text)
        except Exception:
            pass
    info["brief_chars"] = chars
    info["brief"] = brief_text
    return info


def run_marks(layout, style="terse", out_dir="out/marks", model="",
              no_llm=False, grid=44, margin=1, ring=None,
              profile_path="", prebattle_path=""):
    """主流程：规则草案 →（可选）模型补丁 → 校验合并 → 落盘。返回 (calls, meta)。

    ring 可外部注入（探针对比旧环时用）；不传则按当前 deployment_ring 现算。
    profile_path: config/heroes.json；prebattle_path: out/prebattle/info.json。
    """
    from . import equipment, knowledge
    sim, data = _load_sim(layout, grid=grid)
    if ring is None:
        ring = analysis.deployment_ring(sim, margin=margin)
    army = dict(planner.DEFAULT_ARMY)
    report = analysis.defense_report(sim, ring, army)
    plans = analysis.candidate_plans(sim, ring, army, report)
    layout_name = os.path.basename(layout)

    # 装备画像（None 时 build_marks 保持旧行为）
    profile = equipment.load_profile(profile_path) if profile_path else None
    rules = equipment.profile_rules(profile) if profile else None

    # 战术卡检索：只取落盘命中，不编造
    eq_brief = (rules["enabled"] if rules else [])
    kb_brief = {
        "th": (profile or {}).get("th") or 13,
        "army": "edrag",
        "equipment": eq_brief,
        "pattern": "edrag_rush",
        "countered_layout": "ring",
        "keywords": "雷龙 防空 穿云箭",
    }
    cards = knowledge.retrieve(profile=profile, brief=kb_brief, k=3)

    prebattle = _load_prebattle(prebattle_path) if prebattle_path else None

    rule_calls = build_marks(sim, ring, report, plans, army,
                             profile=profile, cards=cards, prebattle=prebattle)

    meta = {
        "layout": layout_name,
        "style": style,
        "ring": {
            "cells": int(ring.sum()),
            "impl": "close_dilate_margin%d" % margin,
            "ring_fix": True,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        },
        "model_used": "",
        "llm_error": "",
        "cache_hit": False,
        "issues": [],
        "applied": [],
        "profile_used": (rules or {}).get("enabled", []),
        "profile_missing": (rules or {}).get("missing", []),
        "cards": [ (c[0] if isinstance(c, tuple) else c).get("id") for c in cards ],
        "prebattle_loaded": bool(prebattle),
    }

    calls = rule_calls
    if not no_llm:
        # 缓存键含 profile/prebattle 指纹，不同装备/情报不串缓存
        fp = hash(json.dumps({"p": eq_brief, "pb": bool(prebattle)}, sort_keys=True))
        cache_key_style = f"marks-{style}-{fp & 0xffff:x}"
        cached = prompts.cache_get(layout_name, plans, cache_key_style)
        if cached:
            meta["cache_hit"] = True
            patch = cached.get("clean") or {}
            meta["model_used"] = cached.get("model_used", "")
            merged, applied = merge_marks(rule_calls, patch, ring=ring, sim=sim)
            calls = merged
            meta["applied"] = applied
            meta["issues"] = cached.get("issues", [])
        else:
            brief = prompts.compact_brief(layout_name, report, plans, army)
            msgs, st = prompts.build_marks_messages(
                brief, rule_calls, style, cards=cards, prebattle=prebattle)
            try:
                from . import llm
                obj, used, raw = llm.chat_json(
                    msgs, model=model or None, max_tokens=st["max_tokens"],
                    retries=0, temperature=0.1)
                patch, issues = validate_marks(obj, ring, sim)
                meta["model_used"] = used
                meta["issues"] = issues
                prompts.cache_put(layout_name, plans, cache_key_style,
                                  {"clean": patch, "model_used": used, "raw": raw,
                                   "issues": issues, "style": style})
                merged, applied = merge_marks(rule_calls, patch, ring=ring, sim=sim)
                calls = merged
                meta["applied"] = applied
            except Exception as e:  # 模型不可用：完整保留规则结果
                meta["llm_error"] = str(e)[:200]
                calls = copy.deepcopy(rule_calls)
                calls["source"] = "rule"

    meta["coord_audit"] = coord_audit(calls, ring)
    return calls, meta


# ---------------- cli 接线入口 ----------------

def cmd_marks(args):
    """与 cli.py 其他 cmd_* 一致：接收 argparse Namespace，返回 0/1。"""
    out_dir = getattr(args, "out", "out/marks") or "out/marks"
    os.makedirs(out_dir, exist_ok=True)
    calls, meta = run_marks(
        layout=args.layout,
        style=getattr(args, "style", "terse"),
        out_dir=out_dir,
        model=getattr(args, "model", "") or "",
        no_llm=getattr(args, "no_llm", False),
        grid=getattr(args, "grid", 44),
        margin=getattr(args, "margin", 1),
        profile_path=getattr(args, "profile", "") or "",
        prebattle_path=getattr(args, "prebattle", "") or "",
    )

    payload = dict(calls)
    payload["source"] = calls.get("source", "rule")
    payload["meta"] = meta

    with open(os.path.join(out_dir, "marks.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # 摘要 txt
    lines = [
        f"layout={meta['layout']} style={meta['style']} source={payload['source']}",
        f"ring cells={meta['ring']['cells']} impl={meta['ring']['impl']} ts={meta['ring']['timestamp']}",
        f"model={meta['model_used'] or '(none)'} cache_hit={meta['cache_hit']} llm_error={meta['llm_error'] or '-'}",
        ("arrow " + json.dumps(calls["lines"][0], ensure_ascii=False)) if calls.get("lines")
            else "arrow (无穿云箭线：giant-arrow 未穿戴)",
        f"profile_used={meta['profile_used']} missing={meta['profile_missing']} cards={meta['cards']}",
        f"pins={len(calls.get('pins', []))} steps={len(calls.get('steps', []))} marks={len(calls.get('marks', []))}",
        f"coord_audit={json.dumps(meta['coord_audit'], ensure_ascii=False)}",
        "applied=" + ",".join(meta["applied"]),
        "issues=" + ";".join(meta["issues"]),
        "",
        "--- steps ---",
    ]
    for i, s in enumerate(calls.get("steps", []), 1):
        lines.append(f"{i}. {s}")
    with open(os.path.join(out_dir, "marks_summary.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(json.dumps({
        "source": payload["source"],
        "arrow": calls["lines"][0] if calls.get("lines") else None,
        "pins": [{"role": p["role"], "tile": p["tile"], "label": p.get("label", "")}
                 for p in calls.get("pins", [])],
        "steps": calls.get("steps", []),
        "coord_audit": meta["coord_audit"],
        "model_used": meta["model_used"],
        "llm_error": meta["llm_error"],
        "out": out_dir,
    }, ensure_ascii=False, indent=2))
    return 0


def _build_parser():
    ap = argparse.ArgumentParser(prog="clashlab.plan_marks",
                                 description="屏幕绘制标注：规则草案 + 模型补丁 → draw_calls")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("marks", help="生成屏幕绘制标注 JSON")
    p.add_argument("--layout", required=True, help="阵型 JSON 路径")
    p.add_argument("--style", default="terse", choices=list(prompts.STYLES.keys()))
    p.add_argument("--out", default="out/marks")
    p.add_argument("--model", default="", help="覆盖模型名；留空走默认回退链")
    p.add_argument("--no-llm", action="store_true", help="跳过模型，纯规则")
    p.add_argument("--grid", type=int, default=44)
    p.add_argument("--margin", type=int, default=1)
    p.add_argument("--profile", default="", help="英雄装备画像 JSON（config/heroes.json）")
    p.add_argument("--prebattle", default="", help="赛前 info.json（out/prebattle/info.json）")
    p.set_defaults(func=cmd_marks)
    return ap


def main(argv=None):
    ap = _build_parser()
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
