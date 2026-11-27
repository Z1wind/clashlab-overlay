# -*- coding: utf-8 -*-
"""ClashKing 公开端点查询 CLI（无需 token）。
  python tools/ck_lookup.py --clan '#PUP9P88R'
  python tools/ck_lookup.py --clan '#PUP9P88R' --wars cwl
  python tools/ck_lookup.py --static 'Town Hall'
"""
import argparse, json, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
from clashlab import cocapi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clan", default=None)
    ap.add_argument("--player", default=None)
    ap.add_argument("--wars", default=None, help="cwl / regular（不传则默认）")
    ap.add_argument("--static", default=None, help="静态数据项名，如 'Town Hall'")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.static:
        print(a.static, "max_level =", cocapi.static_max_level("buildings", a.static))
        return 0
    if a.player:
        doc = cocapi.search_player(a.player, limit=3)
        print(json.dumps(doc, ensure_ascii=False, indent=1)[:1200])
        return 0
    if a.clan:
        doc = cocapi.clan_cached(a.clan)
        th = cocapi.cached_members_th(a.clan)
        dist = {}
        for v in th.values():
            dist[v] = dist.get(v, 0) + 1
        print("clan:", doc.get("name"), doc.get("tag"), "| level:", doc.get("clanLevel"),
              "| members:", doc.get("memberCount"), "| warLeague:", (doc.get("warLeague") or {}).get("name"))
        print("TH 分布:", dict(sorted(dist.items(), reverse=True)))
        if a.wars:
            items = cocapi.clan_wars_filtered(a.clan, war_type=a.wars, limit=5)
            print("wars(%s): %d 条" % (a.wars, len(items)))
            for w in items[:3]:
                print("  ", w.get("state"), w.get("startTime"), "teamSize", w.get("teamSize"),
                      "attacks", len(w.get("attacks") or []))
        if a.json:
            print(json.dumps({"profile": doc, "th": th}, ensure_ascii=False)[:800])
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
