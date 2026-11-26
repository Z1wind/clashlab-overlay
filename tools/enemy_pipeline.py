# -*- coding: utf-8 -*-
"""敌方阵型分析流水线：annotated JSON -> 防守评分 + 弱点 + 穿云箭最优线 + 落点敏感性。

    python tools/enemy_pipeline.py --layout out/annotate/03_annotated.json --out out/enemy_report
"""
import argparse, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layout", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--queen", default=None, help="英雄落点 tile，如 3,20；缺省按对空目标自动选")
    a = ap.parse_args()
    from clashlab.overlay import giant_arrow_diagram as ga
    from clashlab.overlay import arrow_placement as apx
    lay = json.load(open(a.layout, encoding="utf-8"))
    out_dir = a.out or os.path.join(ROOT, "out", "enemy_report")
    os.makedirs(out_dir, exist_ok=True)

    report = {"layout": os.path.relpath(a.layout, ROOT), "name": lay.get("name"),
              "buildings": len(lay.get("buildings") or [])}

    # 1) 评分
    try:
        from clashlab import layout_score
        report["score"] = layout_score.score_layout(lay)
    except Exception as e:
        report["score_error"] = str(e)[:120]

    # 2) 穿云箭自动选线
    opt = ga.optimize_giant_arrow(lay, top=3)
    report["arrow_best"] = opt.get("best")
    report["arrow_candidates"] = opt.get("candidates")

    # 3) 英雄落点敏感性
    if a.queen:
        qx, qy = [float(x) for x in a.queen.split(",")]
    else:
        air = [b for b in lay.get("buildings") or [] if b.get("type") in ("air-sweeper", "air-defense")]
        qx, qy = (3.0, 3.0)
        if air:
            t = air[0]["tile"]
            qx, qy = (1.0 if t[0] < 22 else 43.0), float(t[1])
    res = apx.arrow_from_placement(lay, [qx, qy])
    sens = apx.placement_sensitivity(lay, [qx, qy], radius=0.5, step=0.25)
    report["placement"] = {"queen": [qx, qy], "target": res.get("target"),
                           "angle": res.get("angle_deg"), "hits": len(res.get("hits") or []),
                           "stable": sens["stable"], "distinct": sens["distinct_signatures"],
                           "flips": sens["flips"]}

    path = os.path.join(out_dir, "report.json")
    json.dump(report, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    sc = report.get("score") or {}
    b = report.get("arrow_best") or {}
    p = report["placement"]
    print("布局:", report["name"], "| 建筑:", report["buildings"])
    print("评分:", sc if sc else report.get("score_error"))
    print("穿云箭最优: score=%s 命中=%s" % (b.get("score"), b.get("summary")))
    print("落点 %s: 目标=%s 角度=%s 命中=%d | 稳定=%s 不同结果=%d 翻转=%d" % (
        p["queen"], (p["target"] or {}).get("type"), p["angle"], p["hits"], p["stable"], p["distinct"], p["flips"]))
    print("报告:", os.path.relpath(path, ROOT))

if __name__ == "__main__":
    main()
