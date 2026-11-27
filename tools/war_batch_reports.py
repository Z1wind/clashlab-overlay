# -*- coding: utf-8 -*-
"""批量：战场截图 → 拼图 →（有标注时）逐阵生成报告。"""
import argparse, glob, json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = "C:/Users/Admin（无密码）/Doubao/chats/2026-11-23/new-chat"
sys.path.insert(0, BASE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", default=BASE + "/out/live/war1080/base_*.png")
    ap.add_argument("--labels-dir", default=BASE + "/out/labels")
    ap.add_argument("--thr", type=float, default=0.40)
    ap.add_argument("--th", type=int, default=15)
    a = ap.parse_args()
    from tools.war_base_montage import process
    from tools.labels_to_layout import convert
    from clashlab import battle_report
    imgs = sorted(glob.glob(a.glob))
    print("images:", len(imgs))
    for p in imgs:
        name = os.path.splitext(os.path.basename(p))[0]
        res = process(p, a.thr, BASE + "/out/labels/war")
        lab = os.path.join(a.labels_dir, name + "_labels.json")
        line = {"image": name, "items": res.get("items")}
        if os.path.exists(lab):
            lay = convert(lab, name + "_auto")
            rep = battle_report.build(lay["path"], th=a.th)
            line.update({"report": rep["path"], "grade": rep["grade"], "score": rep["score"]})
        print(json.dumps(line, ensure_ascii=False)[:300])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())