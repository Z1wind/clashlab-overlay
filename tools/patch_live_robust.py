# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"

# 1) ocr_screen: 提取 #TAG
p = os.path.join(BASE, "clashlab", "ocr_screen.py")
t = open(p, encoding="utf-8").read()
if "_TAG_RE" not in t:
    t = t.replace('''# 游戏 UI 文案：不是对手名字/部落，解析前先剔除''',
'''_TAG_RE = re.compile(r"^#?([0-9A-Z]{6,12})$")

# 游戏 UI 文案：不是对手名字/部落，解析前先剔除''')
    t = t.replace('''    name = rest[0] if rest else None
    clan = rest[1] if len(rest) > 1 else None
    return {"level": level, "name": name, "clan": clan}''',
'''    tag = None
    named = []
    for x in rest:
        if tag is None and _TAG_RE.match(x.replace(" ", "")) and any(c.isdigit() for c in x):
            tag = "#" + x.replace("#", "").replace(" ", "").upper()
            continue
        named.append(x)
    name = named[0] if named else None
    clan = named[1] if len(named) > 1 else None
    return {"level": level, "name": name, "clan": clan, "tag": tag}''')
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("tag extraction added")

# 2) cocapi: tag 直接解析 + 歧义告警
p2 = os.path.join(BASE, "clashlab", "cocapi.py")
t2 = open(p2, encoding="utf-8").read()
if "def resolve_by_tag" not in t2:
    add = '''

def resolve_by_tag(tag, fresh=True):
    """OCR 到玩家 tag 时最可靠：直接按 tag 取 TH + 部落战。"""
    tag = "#" + str(tag).strip().lstrip("#").upper()
    th = player_th(tag, fresh=fresh)
    res = {"query": {"tag": tag}, "player": {"name": None, "tag": tag, "th": th},
           "clan": None, "war": None, "match": {"by": "player-tag"},
           "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "fresh": bool(fresh)}
    return res
'''
    t2 = t2.rstrip() + "\n" + add
    open(p2, "w", encoding="utf-8", newline="\n").write(t2)
    print("resolve_by_tag added")

# 3) resolve_opponent 返回歧义告警 + 优先用 tag
t2 = open(p2, encoding="utf-8").read()
old = '''    import time as _t
    res = {"query": {"name": name, "clan": clan_name}, "player": None, "clan": None,'''
new = '''    import time as _t
    if name and str(name).strip().startswith("#"):
        return resolve_by_tag(name, fresh=fresh)
    res = {"query": {"name": name, "clan": clan_name}, "player": None, "clan": None,'''
if old in t2:
    t2 = t2.replace(old, new, 1)
    open(p2, "w", encoding="utf-8", newline="\n").write(t2)
    print("tag-first resolve ok")

# 4) 歧义：所选 player 部落与 OCR 不符且没有 war-member 替换时告警
t2 = open(p2, encoding="utf-8").read()
old2 = '''    # 候选与歧义标记：同名不同部落时提示，避免「看起来成功其实认错人」'''
new2 = '''    if clan_name and pl and _name_score(clan_name, ((pl.get("clan") or {}).get("name") or "")) < 0.5:
        if res.get("match", {}).get("by") != "war-member-fuzzy":
            res["ambiguous"] = True
            res["warning"] = "同名/部落不匹配：请用玩家标签或点选候选确认"

    # 候选与歧义标记：同名不同部落时提示，避免「看起来成功其实认错人」'''
if old2 in t2:
    t2 = t2.replace(old2, new2, 1)
    open(p2, "w", encoding="utf-8", newline="\n").write(t2)
    print("ambiguity warning ok")
