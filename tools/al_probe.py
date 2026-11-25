# -*- coding: utf-8 -*-
"""单点验证回路 v2：tap → 差分定位弹窗 → 放大 OCR → BACK；box 转 int 便于 JSON。"""
import json, os, sys, time
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import al_drive as d
import al_ocr

BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "out", "overlay", "_auto_label")


def probe(points, tag="probe", wait=1.0, save_posts=0):
    os.makedirs(os.path.join(OUT, "probe"), exist_ok=True)
    results = []
    for i, (x, y) in enumerate(points):
        pre = d.shot()
        try:
            d.tap(x, y, "probe")
        except RuntimeError as e:
            results.append({"i": i, "x": x, "y": y, "error": str(e)})
            continue
        time.sleep(wait)
        post = d.shot()
        if i < save_posts:
            d.shot(os.path.join(OUT, "probe", "%s_post_%02d.png" % (tag, i)))
        box = al_ocr.changed_box(pre, post)
        rec = {"i": i, "x": x, "y": y, "box": None, "type": None, "kw": None, "lines": []}
        if box is not None:
            x0, y0, w, h, a = [int(v) for v in box]
            rec["box"] = [x0, y0, w, h, int(a)]
            pad = 10
            xa, ya = max(0, x0 - pad), max(0, y0 - pad)
            xb, yb = min(post.shape[1], x0 + w + pad), min(post.shape[0], y0 + h + pad)
            reg = post[ya:yb, xa:xb]
            pim = al_ocr.preprocess(reg)
            if pim is not None:
                res = al_ocr.ocr(pim)
                lines = [l.get("text", "") for l in res.get("lines", [])]
                typ, kw = al_ocr.classify(" ".join(lines))
                rec.update({"type": typ, "kw": kw, "lines": lines})
                cv2.imencode(".png", reg)[1].tofile(os.path.join(OUT, "probe", "%s_%02d.png" % (tag, i)))
            d.sh(["shell", "input", "keyevent", "4"])
            time.sleep(0.35)
        results.append(rec)
        print("%02d (%4d,%4d) box=%s type=%s" % (i, x, y, "None" if box is None else "Y", rec["type"]))
    json.dump(results, open(os.path.join(OUT, "%s_result.json" % tag), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return results


if __name__ == "__main__":
    tag = sys.argv[1] if len(sys.argv) > 1 else "p2"
    # 当前为全base视野（23.5px/格），在基地内稀疏取 10 点
    PTS = [(640, 360), (520, 300), (760, 300), (640, 250), (520, 420),
           (760, 420), (640, 470), (450, 250), (830, 250), (450, 470)]
    probe(PTS, tag, wait=1.0, save_posts=3)
