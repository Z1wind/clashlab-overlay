# -*- coding: utf-8 -*-
"""A 方案：按 TH 满级回填已标注阵型的建筑等级。

    python tools/apply_max_levels.py --th 16            # 全部 out/annotate/NN_annotated.json
    python tools/apply_max_levels.py --th 16 --base 03
"""
import argparse
import glob
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from clashlab import levels, th_data  # noqa: E402


def fill_file(path, th, overwrite=False):
    doc = json.load(open(path, encoding="utf-8"))
    rows = []
    for b in doc.get("buildings") or []:
        t = str(b.get("type") or "")
        if not t:
            continue
        max_lv = levels.max_level_of(t, th)
        if b.get("level") and not overwrite:
            rows.append({"type": t, "tile": b.get("tile"), "level": b["level"], "kept": True})
            continue
        b["level"] = int(max_lv)
        rows.append({"type": t, "tile": b.get("tile"), "level": int(max_lv)})
    shutil.copyfile(path, path + ".bak_lv")
    json.dump(doc, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--th", type=int, default=16)
    ap.add_argument("--base", default=None)
    ap.add_argument("--overwrite", action="store_true", help="覆盖已有 level（默认只补缺失）")
    a = ap.parse_args()
    paths = (sorted(glob.glob(os.path.join(ROOT, "out", "annotate", "%s_annotated.json" % a.base)))
             if a.base else
             sorted(glob.glob(os.path.join(ROOT, "out", "annotate", "*_annotated.json"))))
    report = {"th": a.th, "files": [], "totals": {"buildings": 0, "types": {}}}
    for p in paths:
        rows = fill_file(p, a.th, overwrite=a.overwrite)
        per_type = {}
        for r in rows:
            per_type[r["type"]] = per_type.get(r["type"], 0) + 1
            report["totals"]["types"][r["type"]] = report["totals"]["types"].get(r["type"], 0) + 1
        report["totals"]["buildings"] += len(rows)
        report["files"].append({"file": os.path.basename(p), "buildings": len(rows),
                                "levels": per_type})
        print("[fill] %s %d 栋 -> 等级已按 TH%d 满级写入（备份 .bak_lv）" % (
            os.path.basename(p), len(rows), a.th))
    out = os.path.join(ROOT, "out", "annotate", "level_fill_report.json")
    json.dump(report, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("report:", out)
    print("types:", json.dumps(report["totals"]["types"], ensure_ascii=False))


if __name__ == "__main__":
    main()
