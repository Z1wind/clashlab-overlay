# -*- coding: utf-8 -*-
"""防守自检 / 攻击建议：输入自己的或对手的阵型 JSON，输出规则评分 + 修复建议 + 推荐打法 + 穿云箭候选。"""
import argparse, json, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layout", required=True)
    ap.add_argument("--th", type=int, default=None)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    lay = json.load(open(a.layout, encoding="utf-8"))
    from clashlab import layout_rules
    from clashlab.overlay import giant_arrow_diagram as ga
    ev = layout_rules.evaluate(lay)
    stairs = ga.optimize_giant_arrow(lay, top=3)
    try:
        from clashlab import strategy
        recs = strategy.recommend(lay, th=a.th, limit=3)
    except Exception as e:
        recs = {"error": str(e)[:200]}
    if a.json:
        print(json.dumps({"rules": ev, "arrow": stairs, "strategy": recs}, ensure_ascii=False, indent=1))
        return 0
    print("# 自检报告：", lay.get("name") or a.layout)
    print("- 规则评分：**%s**（%s），墙体置信度：%s" % (ev["score"], ev["grade"], ev.get("wall_confidence")))
    if ev.get("skipped"):
        print("- 未判定规则（墙数据不足）：", ", ".join(ev["skipped"]))
    fails = ev.get("failed") or []
    if fails:
        print("\n## 需要修的")
        for r in fails:
            print("- [%s] %s：%s → %s" % (r["severity"], r["title"], r["evidence"], r["recommendation"]))
    b = (stairs or {}).get("best") or {}
    if b:
        print("\n## 穿云箭（进攻这一阵的最优线）")
        print("- 起点 %s → 终点 %s，命中 %s 个目标" % (b.get("from"), b.get("to"), len(b.get("hits") or [])))
        for c in (stairs.get("candidates") or [])[:3]:
            print("  - 候选 %s→%s 命中 %s" % (c.get("from"), c.get("to"), len(c.get("hits") or [])))
    # 进攻模拟（启发式，用推荐打法里的兵种）
    try:
        from clashlab import battle_sim
        army = {}
        first = None
        if isinstance(recs, dict):
            _rs = recs.get("recommendations") or recs.get("items") or []
            first = _rs[0] if _rs else None
        elif isinstance(recs, list) and recs:
            first = recs[0]
        if first:
            army = first.get("troops") or {}
        if army:
            sim = battle_sim.simulate(lay, army)
            print("\n## 进攻模拟（启发式）")
            if sim.get("ok"):
                print("- 推荐侧 %s｜路径 %s 格｜破墙 %s｜暴露 DPS %s｜生存率 %.0f%%｜拆本 %ss｜预估星级 %s" % (
                    sim["side"], sim["path_len"], sim["walls_to_break"], sim["exposure_dps"],
                    sim["survival"] * 100, sim["th_ttk_s"], sim["stars_estimate"]))
            else:
                print("- 无法模拟:", sim.get("error"))
    except Exception as e:
        print("\n## 进攻模拟：失败（%s）" % str(e)[:100])
    if isinstance(recs, dict) and recs.get("error"):
        print("\n## 推荐打法：数据缺失（%s）" % recs["error"])
    else:
        print("\n## 推荐打法")
        print(json.dumps(recs, ensure_ascii=False)[:1200])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
