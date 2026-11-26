# -*- coding: utf-8 -*-
"""批量给 layout 的建筑写等级。

    python tools/set_levels.py --layout bases/th16/03/layout.json --levels cannon=16,x-bow=5
    python tools/set_levels.py --layout ... --levels archer-tower=10 --out out/layout_lv.json
"""
import argparse
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from clashlab import levels  # noqa: E402


def parse_levels(text):
    out = {}
    for part in str(text or "").split(","):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            raise ValueError("等级格式应为 type=level：%r" % part)
        k, v = part.split("=", 1)
        out[k.strip()] = int(v)
    return out


def main():
    ap = argparse.ArgumentParser(description="批量设置 layout 建筑等级（写回 level 字段）")
    ap.add_argument("--layout", required=True)
    ap.add_argument("--levels", required=True, help="例如 cannon=16,x-bow=5")
    ap.add_argument("--th", type=int, default=None)
    ap.add_argument("--out", default=None, help="输出路径（默认原地写，先备份 .bak）")
    ap.add_argument("--no-backup", action="store_true")
    a = ap.parse_args()
    doc = json.load(open(a.layout, encoding="utf-8"))
    want = parse_levels(a.levels)
    th = a.th
    if th is None:
        import re
        m = re.search(r"th(\d{1,2})", str(doc.get("name") or a.layout), re.I)
        th = int(m.group(1)) if m else 16
    n = 0
    for b in doc.get("buildings") or []:
        typ = str(b.get("type") or "")
        if typ in want:
            mx = levels.max_level_of(typ, th)
            lv, _ = levels.clamp_level(want[typ], mx)
            b["level"] = lv
            n += 1
    out = a.out or a.layout
    if out == a.layout and not a.no_backup:
        shutil.copyfile(a.layout, a.layout + ".bak")
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    json.dump(doc, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("[set-levels] th=%d 命中 %d 栋，写入 %s（等级：%s）" % (
        th, n, out, ", ".join("%s=%d" % (k, v) for k, v in want.items())))


if __name__ == "__main__":
    main()
