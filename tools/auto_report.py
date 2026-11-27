# -*- coding: utf-8 -*-
"""减少工作量版入口：
  python tools/auto_report.py --layout out/annotate/06_annotated.json
  python tools/auto_report.py --image out/live/x.png            # 自动标定 + 找同名标注 + 出报告
  python tools/auto_report.py --dir out/annotate                # 批量：所有 *_annotated.json
自动标定失败时只输出可点击的网格预览 + 操作指引，不猜坐标。
"""
import argparse, glob, json, os, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
PY = sys.executable


def run(cmd):
    r = subprocess.run([PY, "-u"] + cmd, capture_output=True, text=True, cwd=BASE)
    if r.returncode != 0:
        print("FAIL:", " ".join(cmd), "\n", (r.stderr or r.stdout)[-500:])
    return r.returncode, r.stdout


def calib_sane(quad, w, h):
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
    return Calib.from_quad(np.asarray(quad, np.float32), n=44), meta, img


def grid_preview(img_path, cal, img, out_png):
    import cv2, numpy as np
    vis = img.copy()
    for i in range(0, 45, 2):
        p0 = cal.tile_to_px(i, 0); p1 = cal.tile_to_px(i, 44)
        q0 = cal.tile_to_px(0, i); q1 = cal.tile_to_px(44, i)
        cv2.line(vis, (int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])), (0, 255, 0), 1)
        cv2.line(vis, (int(q0[0]), int(q0[1])), (int(q1[0]), int(q1[1])), (0, 255, 0), 1)
    cv2.imencode(".png", vis)[1].tofile(out_png)
    return out_png


def find_layout_for(img_path):
    stem = os.path.splitext(os.path.basename(img_path))[0]
    for cand in (os.path.join(BASE, "out", "annotate", stem + "_annotated.json"),
                 os.path.join(BASE, "out", "annotate", stem + ".json")):
        if os.path.exists(cand):
            return cand
    return None


def report(layout_path, out_dir=None):
    cmd = ["tools/report_one.py", "--layout", layout_path]
    if out_dir:
        cmd += ["--out", out_dir]
    return run(cmd)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layout", default=None)
    ap.add_argument("--image", default=None)
    ap.add_argument("--dir", default=None)
    ap.add_argument("--quad", default=None, help="四角像素，分号分隔：x1,y1;x2,y2;x3,y3;x4,y4")
    a = ap.parse_args()
    if a.layout:
        print("report ->", a.layout)
        return report(a.layout)[0]
    if a.dir:
        lays = sorted(glob.glob(os.path.join(a.dir, "*_annotated.json")))
        print("batch:", len(lays), "layouts")
        fails = 0
        for lay in lays:
            rc, out = report(lay)
            fails += 1 if rc else 0
            print(" ", os.path.basename(lay), "OK" if rc == 0 else "FAIL")
        print("batch done, failures:", fails)
        return 1 if fails else 0
    if not a.image:
        ap.print_help(); return 2
    if not os.path.exists(a.image):
        print("image not found:", a.image); return 2
    lay = find_layout_for(a.image)
    if lay:
        print("found layout:", lay)
        return report(lay)[0]
    if a.quad:
        import cv2, numpy as np
        from clashlab.geo import Calib
        pts = np.array([[float(v) for v in p.split(",")] for p in a.quad.split(";")], np.float32)
        img = cv2.imdecode(np.fromfile(a.image, np.uint8), cv2.IMREAD_COLOR)
        cal = Calib.from_quad(pts, n=44)
        out_png = os.path.join(BASE, "out", "live", os.path.splitext(os.path.basename(a.image))[0] + "_grid.png")
        grid_preview(a.image, cal, img, out_png)
        print("quad applied -> grid preview:", out_png)
        print("下一步：标注建筑后运行 tools/report_one.py --layout <json>")
        return 0
    cal, meta, img = calibrate(a.image)
    if cal is None:
        print("自动标定失败（method=%s, area_frac=%s, side_ratio=%s）。" % (meta.get("method"), meta.get("area_frac"), meta.get("side_ratio")))
        print("请用标注器点 4 角，或传 --quad \"x1,y1;x2,y2;x3,y3;x4,y4\"")
        print("标定成功后可一键出报告；已标注的阵可直接 --layout。")
        return 3
    out_png = os.path.join(BASE, "out", "live", os.path.splitext(os.path.basename(a.image))[0] + "_grid_auto.png")
    grid_preview(a.image, cal, img, out_png)
    print("自动标定成功（method=%s）-> %s" % (meta.get("method"), out_png))
    print("该图暂无标注文件；mass 标注后一条命令出报告：tools/report_one.py --layout <json>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
