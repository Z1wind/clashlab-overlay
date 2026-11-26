# -*- coding: utf-8 -*-
"""从对战截图 OCR 对手名字/部落，并用公开 API 解析 tag/TH/部落战（默认强制拉最新）。

    python tools\\ocr_opponent.py --image out\\ocr_test.png
    python tools\\ocr_opponent.py --image out\\ocr_test.png --no-api
"""
import argparse
import json
import os
import sys
import time

import numpy as np
import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
from clashlab import cocapi, ocr_screen  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--no-api", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    img = cv2.imdecode(np.fromfile(a.image, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise SystemExit("读不到图片: " + a.image)
    got = ocr_screen.read_opponent(img)
    print("[ocr] level=%r name=%r clan=%r" % (got["level"], got["name"], got["clan"]))
    for ln in got["lines"]:
        print("   %.2f  %s" % (ln["score"], ln["text"]))
    payload = {"ocr": got, "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "api": None}
    if not a.no_api and (got["name"] or got["clan"]):
        t0 = time.time()
        res = cocapi.resolve_opponent(got["name"], got["clan"], fresh=True, ocr_level=got.get("level"))
        payload["api"] = res
        payload["api_elapsed_s"] = round(time.time() - t0, 2)
        p = res.get("player") or {}
        c = res.get("clan") or {}
        print("[api] player=%s tag=%s TH=%s | clan=%s %s" % (
            p.get("name"), p.get("tag"), p.get("th"), c.get("name"), c.get("tag")))
        war = res.get("war")
        if war:
            print("[war] state=%s %dv%d 双方成员 TH：" % (war["state"], war["team_size"], war["team_size"]))
            for side in ("clan", "opponent"):
                ms = war[side]["members"]
                print("  %s: %s" % (side, ", ".join("%s TH%s" % (m["name"], m["th"]) for m in ms[:8])))
    if a.out:
        json.dump(payload, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("[out]", a.out)


if __name__ == "__main__":
    main()
