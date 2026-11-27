# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "auto_report.py")
t = open(p, encoding="utf-8").read()
old = '''def calibrate(img_path):
    import cv2, numpy as np
    from clashlab import calib as C
    from clashlab.geo import Calib
    img = cv2.imdecode(np.fromfile(img_path, np.uint8), cv2.IMREAD_COLOR)
    cal, meta = C.detect_village_quad(img, grid_n=44)
    quad = meta.get("quad")
    if cal is None or not quad:
        return None, meta, img
    return Calib.from_quad(np.asarray(quad, np.float32), n=44), meta, img'''
new = '''def calib_sane(quad, w, h):
    """几何合理性：凸、面积占比 12%-40%、边长比 <2.5。挡住草地/墙体误检。"""
    import numpy as np
    q = np.asarray(quad, np.float32).reshape(4, 2)
    area = 0.5 * abs(float(np.dot(q[:, 0], np.roll(q[:, 1], -1)) - np.dot(q[:, 1], np.roll(q[:, 0], -1))))
    frac = area / float(w * h)
    convex = True
    signs = []
    for i in range(4):
        a, b, c = q[i], q[(i + 1) % 4], q[(i + 2) % 4]
        cross = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        signs.append(cross > 0)
    convex = all(signs) or not any(signs)
    sides = [float(np.linalg.norm(q[(i + 1) % 4] - q[i])) for i in range(4)]
    ratio = max(sides) / max(1e-6, min(sides))
    ok = convex and 0.12 <= frac <= 0.40 and ratio <= 2.5
    return ok, {"area_frac": round(frac, 3), "convex": convex, "side_ratio": round(ratio, 2)}


def calibrate(img_path):
    import cv2, numpy as np
    from clashlab import calib as C
    from clashlab.geo import Calib
    img = cv2.imdecode(np.fromfile(img_path, np.uint8), cv2.IMREAD_COLOR)
    cal, meta = C.detect_village_quad(img, grid_n=44)
    quad = meta.get("quad")
    if cal is None or not quad:
        return None, meta, img
    ok, info = calib_sane(quad, img.shape[1], img.shape[0])
    meta.update(info)
    if not ok:
        meta["method"] = (meta.get("method") or "?") + "+rejected"
        return None, meta, img
    return Calib.from_quad(np.asarray(quad, np.float32), n=44), meta, img'''
if old in t:
    t = t.replace(old, new, 1)
    # 失败信息带原因
    t = t.replace('        print("自动标定失败（method=%s）。" % meta.get("method"))',
                  '        print("自动标定失败（method=%s, area_frac=%s, side_ratio=%s）。" % (meta.get("method"), meta.get("area_frac"), meta.get("side_ratio")))')
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("calib sanity gate added")
else:
    print("anchor miss")
