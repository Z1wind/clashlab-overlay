# -*- coding: utf-8 -*-
"""CLI：用 ClashKing 公开 API 自动拿 TH 等级 / 战争成员，并回填布局等级。

    python tools/cocapi_cli.py --player '#QCRJPL2RJ'
    python tools/cocapi_cli.py --clan '#2GYU8JRPV'
    python tools/cocapi_cli.py --auto-levels out/annotate/03_annotated.json --th 16
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
from clashlab import cocapi  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--player", default=None)
    ap.add_argument("--clan", default=None)
    ap.add_argument("--auto-levels", default=None)
    ap.add_argument("--th", type=int, default=None)
    ap.add_argument("--search-name", default=None, help="按玩家名字搜 tag/TH")
    ap.add_argument("--search-clan", default=None, help="按部落名字搜 tag")
    a = ap.parse_args()
    if a.player:
        th = cocapi.player_th(a.player)
        items = cocapi.player_war_attacks(a.player)
        print("玩家 %s -> TH %s（依据 %d 条最近攻防记录）" % (a.player, th, len(items)))
        for it in items[:3]:
            print("  %s vs %s | TH%s vs TH%s | %s星 %s%%" % (
                it.get("attackerName"), it.get("defenderName"),
                it.get("attackerTownhall"), it.get("defenderTownhall"),
                it.get("stars"), it.get("destructionPercentage")))
    if a.clan:
        w = cocapi.war_members(a.clan)
        if not w:
            print("没有找到战争记录"); return
        print("部落战 %s | %dv%d | %s -> %s" % (w["state"], w["team_size"], w["team_size"],
                                             w["start_time"], w["end_time"]))
        for side in ("clan", "opponent"):
            ms = w[side]["members"]
            print(" %s(%s) %d 人：" % (side, w[side]["tag"], len(ms)))
            print("   ", ", ".join("%s TH%s" % (m["name"], m["th"]) for m in ms[:8]))
    if a.search_name or a.search_clan:
        r = cocapi.resolve_opponent(a.search_name, a.search_clan)
        print(json.dumps(r, ensure_ascii=False, indent=1)[:2000])
    if a.auto_levels:
        th = a.th or 16
        doc = json.load(open(a.auto_levels, encoding="utf-8"))
        res = cocapi.apply_th_levels(doc, th)
        json.dump(doc, open(a.auto_levels, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("回填等级 th=%d: %s" % (th, res))


if __name__ == "__main__":
    main()
