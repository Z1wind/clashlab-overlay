# -*- coding: utf-8 -*-
"""简化战斗模拟 CLI（启发式）：
  python tools/sim_attack.py --layout out/annotate/06_annotated.json --army hybrid-miner
  python tools/sim_attack.py --layout x.json --troops "miner=21,hog-rider=11,healer=4"
"""
import argparse, json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
from clashlab import battle_sim, strategy


def load_army(spec):
    spec = spec or {}
    if spec.get("army"):
        try:
            recs = strategy.recommend(None, th=spec.get("th"), limit=8)
            if isinstance(recs, dict):
                recs = recs.get("recommendations") or recs.get("items") or []
            for r in recs or []:
                if r.get("id") == spec["army"]:
                    return r.get("troops") or {}, r.get("spells") or {}
        except Exception as e:
            print("strategy lookup failed:", str(e)[:120])
    if spec.get("troops"):
        out = {}
        for part in spec["troops"].split(","):
            if "=" in part:
                k, v = part.split("=", 1)
                out[k.strip()] = int(v)
        return out, {}
    return {}, {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layout", required=True)
    ap.add_argument("--army", default=None)
    ap.add_argument("--troops", default=None)
    ap.add_argument("--th", type=int, default=None)
    ap.add_argument("--compare", action="store_true", help="对比 3 种配比")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    lay = json.load(open(a.layout, encoding="utf-8"))
    if a.compare:
        from clashlab import battle_sim
        PRESETS = {
            "ground": ({"root-rider": 6, "golem": 3, "witch": 6, "healer": 4},
                       {"rage": 2, "heal": 2, "freeze": 1, "jump": 1}, ["queen", "king", "warden"]),
            "air": ({"edrag": 8, "balloon": 12, "healer": 4},
                    {"rage": 2, "freeze": 2, "haste": 1}, ["queen", "warden"]),
            "hybrid": ({"miner": 21, "hog-rider": 11, "healer": 4},
                       {"heal": 3, "rage": 2}, ["queen", "king"]),
        }
        rows = []
        for name, (army, spells, heroes) in PRESETS.items():
            r = battle_sim.simulate(lay, army, spells=spells, th=a.th, heroes=heroes)
            rows.append((name, army, spells, heroes, r))
        if a.json:
            print(json.dumps([{"comp": n, "result": r} for n, _a, _s, _h, r in rows], ensure_ascii=False, indent=1))
            return 0
        print("# 配比对比（启发式）:", lay.get("name") or a.layout)
        print("%-8s %-7s %-8s %-8s %-8s %-6s" % ("配比", "星级", "生存%", "拆本s", "兵力DPS", "破墙"))
        for name, army, spells, heroes, r in rows:
            if not r.get("ok"):
                print("%-8s 失败: %s" % (name, r.get("error"))); continue
            print("%-8s %-7s %-8.0f %-8s %-8s %-6s" % (
                name, r["stars_estimate"], r["survival"] * 100, r["th_ttk_s"], r["army_dps"], r["walls_to_break"]))
        return 0
    army, spells = load_army({"army": a.army, "troops": a.troops, "th": a.th})
    if not army:
        army = {"miner": 21, "hog-rider": 11, "healer": 4}
        print("army 未指定，用默认 hybrid-miner:", army)
    r = battle_sim.simulate(lay, army)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=1)); return 0
    if not r.get("ok"):
        print("模拟失败:", r.get("error")); return 2
    print("# 进攻模拟（启发式）:", lay.get("name") or a.layout)
    print("- 推荐进攻侧：%s | 路径 %d 格（代价 %.1f）| 需破墙 %d 格" % (
        r["side"], r["path_len"], r["path_cost"], r["walls_to_break"]))
    print("- 暴露 DPS：%d | 路径时间：%ss | 部队 HP：%d | 部队 DPS：%d" % (
        r["exposure_dps"], r["time_on_path_s"], r["army_hp"], r["army_dps"]))
    print("- 预估承伤：%d | 生存率：%.0f%% | 拆大本：%ss | 预估星级：%d" % (
        r["damage_taken"], r["survival"] * 100, r["th_ttk_s"], r["stars_estimate"]))
    if r.get("top_defenses"):
        print("- 路径上威胁最大：", ", ".join("%s(%s格,%ddps)" % (d["type"], d["dist"], d["dps"]) for d in r["top_defenses"]))
    print("- 说明：", r["note"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
