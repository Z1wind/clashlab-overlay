# -*- coding: utf-8 -*-
"""实测 ClashKing 公开端点（真实部落/玩家 tag），记录状态与字段。"""
import json, sys, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = "https://api.clashk.ing"
CLAN = urllib.parse.quote("#PLVYQ0G2U"); PLAYER = urllib.parse.quote("#20R9PL0VU")
EPS = [
 "/v2/clan/%s/cached" % CLAN,
 "/v2/clan/%s/wars" % CLAN,
 "/v2/clan/%s/records" % CLAN,
 "/v2/clan/%s/rankings" % CLAN,
 "/v2/clan/%s/member-joins" % CLAN,
 "/v2/cwl/%s/seasons" % CLAN,
 "/v2/cwl/%s/group" % CLAN,
 "/v2/clan/%s/donations/summary" % CLAN,
 "/v2/player/%s/warhits" % PLAYER,
 "/v2/player/%s/join-leave" % PLAYER,
 "/v2/player/%s/history/legends" % PLAYER,
 "/v2/dates/seasons",
 "/v2/dates/raid-weekends",
 "/v2/counts/players/town-halls",
 "/v2/leaderboard/clan/win-streak",
 "/v2/health",
]
def get(path):
    try:
        with urllib.request.urlopen(urllib.request.Request(BASE + path, headers={"User-Agent": "clashlab"}), timeout=25) as r:
            return r.status, r.read(4000).decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read(300).decode("utf-8", "ignore")
    except Exception as e:
        return "ERR", str(e)[:100]
for ep in EPS:
    st, body = get(ep)
    keys = ""
    try:
        j = json.loads(body)
        if isinstance(j, dict):
            keys = "keys=" + str(list(j.keys())[:7])
            for k in ("items", "data", "response"):
                if k in j and isinstance(j[k], list):
                    keys += " | %s[%d] sample_keys=%s" % (k, len(j[k]), list(j[k][0].keys())[:6] if j[k] and isinstance(j[k][0], dict) else "")
                    break
        else:
            keys = "list[%d]" % len(j)
    except Exception:
        keys = body.replace("\n", " ")[:80]
    print("%-52s %-4s %s" % (ep[:52], st, keys[:170]))
