# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "cocapi.py")
t = open(p, encoding="utf-8").read()
if "def clan_th_distribution(" not in t:
    anchor = "def _enc_url(s):"
    add = '''def clan_th_distribution(clan_tag, fresh=False):
    """部落成员 TH 分布：{"map": {tag: th}, "dist": {th: count}}（免费 cached 端点）。"""
    th = cached_members_th(clan_tag, fresh=fresh)
    dist = {}
    for v in th.values():
        dist[v] = dist.get(v, 0) + 1
    return {"map": th, "dist": dist}


'''
    t = t.replace(anchor, add + anchor, 1)
    # resolve_opponent 尾部附加
    old = '''            except Exception:
                res["war"] = None
    return res'''
    new = '''            except Exception:
                res["war"] = None
    # 4) 免费 cached 端点：部落成员 TH 分布（无需 token）
    _tag = ((res.get("clan") or {}).get("tag")
            or ((res.get("player") or {}).get("clan") or {}).get("tag"))
    if _tag:
        try:
            _d = clan_th_distribution(_tag, fresh=fresh)
            res["clan_th_map"] = _d["map"]
            res["clan_th_dist"] = _d["dist"]
        except Exception:
            pass
    return res'''
    if old in t:
        t = t.replace(old, new, 1)
        open(p, "w", encoding="utf-8", newline="\n").write(t)
        print("cocapi: clan_th_distribution + resolve attach")
    else:
        print("tail anchor miss")
else:
    print("already")
# ocr_job payload
p2 = os.path.join(BASE, "clashlab", "ocr_job.py")
t2 = open(p2, encoding="utf-8").read()
if "clan_th_dist" not in t2:
    old2 = '''    payload = {"ocr": got, "api": api, "th": th,'''
    new2 = '''    payload = {"ocr": got, "api": api, "th": th,
               "clan_th_map": (api or {}).get("clan_th_map") if api else None,
               "clan_th_dist": (api or {}).get("clan_th_dist") if api else None,'''
    if old2 in t2:
        t2 = t2.replace(old2, new2, 1)
        open(p2, "w", encoding="utf-8", newline="\n").write(t2)
        print("ocr_job: clan_th_dist in payload")
    else:
        print("ocr payload anchor miss")
