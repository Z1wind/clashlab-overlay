# -*- coding: utf-8 -*-
"""侦察截图 → 候选拼图 →（有标注时）布局 JSON → 战报，一条命令。

python tools/scout_to_report.py --image out/live/war1080/base_01.png --labels out/labels/base1_labels.json --name enemy1 --th 15
"""
import argparse, json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--labels", default=None)
    ap.add_argument("--name", default=None)
    ap.add_argument("--thr", type=float, default=0.40)
    ap.add_argument("--quad", default=None)
    ap.add_argument("--th", type=int, default=None)
    a = ap.parse_args()
    from tools.war_base_montage import process
    import tools.war_base_montage as wbm
    if a.quad:
        wbm._FORCE_QUAD = [[float(v) for v in part.split(",")] for part in a.quad.split(";")]
    outdir = os.path.join(BASE, "out", "labels", "war")
    res = process(a.image, a.thr, outdir)
    print(json.dumps(res, ensure_ascii=False)[:400])
    if not res.get("ok"):
        print("montage failed"); return 2
    if not a.labels:
        print("no labels -> stop at montage")
        return 0
    from tools.labels_to_layout import convert
    name = a.name or os.path.splitext(os.path.basename(a.image))[0]
    lay = convert(a.labels, name, os.path.join(BASE, "out", "annotate", name + "_auto.json"))
    print("layout:", lay)
    from clashlab import battle_report
    rep = battle_report.build(lay["path"], th=a.th)
    print("report:", rep["path"], rep["bytes"], "bytes | grade", rep["grade"], rep["score"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
