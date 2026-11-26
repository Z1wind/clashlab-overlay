# -*- coding: utf-8 -*-
"""按布阵推荐兵种搭配与打法链接（YouTube 搜索入口）。

用法：
    python tools/strategy_cli.py --layout bases/th16/03/layout.json --th 16
    python tools/strategy_cli.py --layout bases/th16/03/layout.json --th 16 --json

人类可读输出：判定依据 / 信号 / 推荐（兵种、为什么、投放步骤、搜索链接）/ 英雄装备参考。
JSON 输出：layout 摘要 + th + reason + signals + recommendations + hero_equipment。
"""
from __future__ import annotations

import argparse
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from clashlab import strategy  # noqa: E402


def _signal_summary(signals):
    m = {str(s.get("name")): s.get("value") for s in (signals or []) if isinstance(s, dict)}

    def num(key, fmt="%.0f"):
        v = m.get(key)
        return "?" if v is None else fmt % float(v)

    return ("对空 %s%% / 对地 %s%% / 大本营中心度 %s / 有效隔间 %s / 防御 %s / 墙 %s"
            % (num("air-coverage"), num("ground-coverage"),
               num("th-centrality", "%.2f"), num("useful-compartments"),
               num("defenses"), num("walls")))


def _troop_line(troops):
    return ", ".join("%s×%d" % (strategy.TROOP_NAMES_ZH.get(k, k), n)
                     for k, n in (troops or {}).items())


def _spell_line(spells):
    return ", ".join("%s×%d" % (strategy.SPELL_NAMES_ZH.get(k, k), n)
                     for k, n in (spells or {}).items())


def main(argv=None):
    ap = argparse.ArgumentParser(description="布阵 -> 兵种搭配推荐（含 YouTube 搜索链接）")
    ap.add_argument("--layout", required=True, help="layout.json 路径")
    ap.add_argument("--th", type=int, default=16, help="大本营等级（默认 16）")
    ap.add_argument("--limit", type=int, default=3, help="最多推荐几条（默认 3）")
    ap.add_argument("--json", action="store_true", help="输出 JSON（供面板/脚本消费）")
    a = ap.parse_args(argv)

    try:
        with open(a.layout, "r", encoding="utf-8") as f:
            lay = json.load(f)
        if not isinstance(lay, dict):
            raise ValueError("layout 必须是 JSON 对象")
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print("[strategy] 读取布局失败: %s" % (e,), file=sys.stderr)
        return 2

    try:
        reason, signals = strategy.detect_signals(lay)
        recs = strategy.recommend(lay, th=a.th, limit=a.limit)
        equipment = strategy.hero_loadout(a.th)
    except (OSError, ValueError) as e:
        print("[strategy] 推荐失败: %s" % (e,), file=sys.stderr)
        return 2

    if a.json:
        payload = {
            "layout": {
                "name": lay.get("name", ""),
                "grid": lay.get("grid", 44),
                "buildings": len(lay.get("buildings") or []),
                "walls": len(lay.get("walls") or []),
            },
            "th": a.th,
            "reason": reason,
            "reason_label": strategy.REASON_LABEL.get(reason, reason),
            "signals": signals,
            "recommendations": recs,
            "hero_equipment": equipment,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("布局：%s  TH%d" % (lay.get("name", "(unnamed)"), a.th))
    print("推荐：%d 条" % len(recs))
    print("判定：%s（%s）" % (reason, strategy.REASON_LABEL.get(reason, reason)))
    print("信号：%s" % _signal_summary(signals))
    if not recs:
        print("\n没有可用推荐（数据缺失）。")
        return 0

    for i, r in enumerate(recs, 1):
        print("\n%d. %s  [%s / %s / 置信度 %.2f]"
              % (i, r.get("name", ""), r.get("archetype", ""),
                 r.get("reason", ""), float(r.get("confidence") or 0.0)))
        print("   为什么：%s" % (r.get("why") or ""))
        print("   兵种：%s" % (_troop_line(r.get("troops")) or "（无）"))
        if r.get("spells"):
            print("   法术：%s" % _spell_line(r.get("spells")))
        print("   投放顺序：")
        for j, s in enumerate(r.get("steps") or [], 1):
            print("     %d) %s" % (j, s))
        print("   视频（搜索入口，不存储第三方内容）：")
        for v in r.get("videos") or []:
            print("     - %s  %s" % (v.get("title", ""), v.get("url", "")))

    heroes = equipment.get("heroes") or {}
    if heroes:
        print("\n英雄装备参考（仅参考，非实测最优）：")
        for hero, info in heroes.items():
            eq = ", ".join((info or {}).get("equipment") or [])
            print(" - %s：%s" % (strategy.HERO_NAMES_ZH.get(hero, hero), eq or "（待补）"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
