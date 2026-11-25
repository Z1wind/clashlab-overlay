# -*- coding: utf-8 -*-
"""规则化计划器：从撒兵热图生成可序列化、可校验、可回放的 Plan 对象。"""
import time

DEFAULT_ARMY = {
    "name": "雷龙平推",
    "troops": {"edrag": 7, "balloon": 8},
    "hp": 6200.0,
    "dps": 1150.0,
    "speed": 1.5,
}

TROOP_HP = {"edrag": 900.0, "balloon": 320.0, "dragon": 700.0}


def build_plan(sim, ring_mask, army=None, layout_id="live", topk=4):
    """把热图结果落成计划：分批撒兵、分批时间、法术点、终止条件。"""
    army = army or DEFAULT_ARMY
    t0 = time.perf_counter()

    spawns = sim.top_spawns(ring_mask, army, k=topk)
    if not spawns:
        return None

    total_score = sum(max(s["score"], 1e-6) for s in spawns)
    budget = int(army["troops"].get("edrag", 7))
    entry = []
    t = 0.0
    for i, s in enumerate(spawns):
        weight = max(s["score"], 1e-6) / total_score
        count = max(1, int(round(budget * weight)))
        if i == len(spawns) - 1:
            count = max(1, budget)          # 最后一批把剩余兵力吃掉，避免库存校验失败
        count = min(count, max(budget, 1))
        budget -= count
        entry.append({
            "step": i + 1,
            "t": round(t, 1),
            "tile": [int(s["tile"][0]), int(s["tile"][1])],
            "troop": "edrag",
            "count": count,
            "score": s["score"],
            "angle": s["angle"],
        })
        t += 1.6 + 0.2 * i

    # 法术点：取防御密度最高且靠近核心的位置
    best = None
    for b in sim.buildings:
        dens = float(sim.dps[max(0, b["tile"][0] - 3):b["tile"][0] + 4,
                            max(0, b["tile"][1] - 3):b["tile"][1] + 4].sum())
        if best is None or dens > best[0]:
            best = (dens, b["tile"])
    spells = []
    if best:
        spells.append({"t": 4.0, "tile": [int(best[1][0]), int(best[1][1])], "type": "rage"})

    plan = {
        "version": 1,
        "layout_id": layout_id,
        "army": {"edrag": army["troops"].get("edrag", 7), "balloon": army["troops"].get("balloon", 8)},
        "entry": entry,
        "abilities": [{"t": 12.0, "hero": "queen", "skill": "auto"}],
        "spells": spells,
        "siege": None,
        "contingencies": [{"if": "destruction<0.35 and t>90", "then": "shift_to_next_entry"}],
        "abort": {"max_time": 170, "min_destruction": 0.6},
        "predicted": round(min(sum(s["score"] for s in spawns) / max(len(spawns), 1), 1.0), 3),
        "elapsed_ms": round((time.perf_counter() - t0) * 1000, 1),
    }
    return plan


def validate(plan, sim, ring_mask, army=None, baseline=0.0):
    """五项检查：结构、库存、部署区、时间预算、模拟得分。"""
    reasons = []
    if not plan or "entry" not in plan or not plan["entry"]:
        return False, ["schema"]
    n = sim.n
    for e in plan["entry"]:
        x, y = e["tile"]
        if not (0 <= x <= n and 0 <= y <= n) or not ring_mask[x, y]:
            reasons.append("deploy_zone")
            break
    used = {}
    for e in plan["entry"]:
        used[e["troop"]] = used.get(e["troop"], 0) + e["count"]
    cap = (army or DEFAULT_ARMY)["troops"]
    for k, v in used.items():
        if v > cap.get(k, 0):
            reasons.append("inventory")
            break
    if plan["abort"]["max_time"] > 180:
        reasons.append("time_budget")
    if plan.get("predicted", 0) < baseline:
        reasons.append("weak_plan")
    return (len(reasons) == 0), reasons
