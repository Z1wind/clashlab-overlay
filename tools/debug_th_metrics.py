# -*- coding: utf-8 -*-
import json, urllib.parse, urllib.request, collections
TAG = "QCRJPL2RJ"
enc = urllib.parse.quote("#" + TAG)
req = urllib.request.Request("https://api.clashk.ing/v2/player/%s/war/attacks" % enc, headers={"User-Agent": "clashlab"})
items = json.loads(urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "ignore")).get("items") or []
cnt_def = collections.Counter(); cnt_atk = collections.Counter()
for it in items:
    if str(it.get("defenderTag") or "").lstrip("#").upper() == TAG:
        cnt_def[int(it.get("defenderTownhall") or 0)] += 1
    if str(it.get("attackerTag") or "").lstrip("#").upper() == TAG:
        cnt_atk[int(it.get("attackerTownhall") or 0)] += 1
print("defense TH counts:", dict(cnt_def))
print("attack TH counts:", dict(cnt_atk))
print("total items:", len(items))

# 最终训练指标
m = json.load(open(r"E:\ClashLab\models\synth_level_metrics.json", encoding="utf-8"))
print("synth metrics:", json.dumps({k: m[k] for k in ("n", "train", "val", "types", "epochs", "type_acc", "level_mae")}, ensure_ascii=False))
print("per_type level mae (部分):", json.dumps(dict(list((m.get("per_type_level_mae") or {}).items())[:8]), ensure_ascii=False))
