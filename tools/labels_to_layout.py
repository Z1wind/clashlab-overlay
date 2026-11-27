# -*- coding: utf-8 -*-
"""把标注（quad + tile/size/type）转成 layout JSON，供评分/模拟/战报使用。

python tools/labels_to_layout.py --labels out/labels/real_labels.json --name enemy_th15 --out out/annotate/enemy_th15_auto.json
"""
import argparse, json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"


def convert(labels_path, name=None, out_path=None):
    doc = json.load(open(labels_path, encoding="utf-8"))
    items = doc.get("items") or []
    buildings = []
    for it in items:
        t = it.get("type")
        if not t or t == "__bg__" or not it.get("tile"):
            continue
        buildings.append({"type": t, "tile": [int(it["tile"][0]), int(it["tile"][1])]})
    layout = {"name": name or "auto_layout", "grid": 44, "buildings": buildings,
              "walls": doc.get("walls") or [],
              "note": "auto from screenshot labels; source=%s" % os.path.basename(labels_path)}
    out_path = out_path or os.path.join(BASE, "out", "annotate", layout["name"] + "_auto.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    json.dump(layout, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return {"ok": True, "path": out_path, "buildings": len(buildings),
            "types": len({b["type"] for b in buildings})}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", required=True)
    ap.add_argument("--name", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    r = convert(a.labels, a.name, a.out)
    print(json.dumps(r, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
