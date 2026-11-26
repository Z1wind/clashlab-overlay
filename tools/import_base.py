# -*- coding: utf-8 -*-
"""从游戏画面导入一个新阵型：截屏/读图 -> 自动标定 44×44 -> 生成 base.png + layout_draft.json。

用法（在模拟器里点开阵型分享链接、进入阵型预览后）：
    python tools/import_base.py --th 16 --id 07
    python tools/import_base.py --th 16 --id 07 --from-file out/shot.png
    python tools/import_base.py --th 16 --id 07 --copy-from bases/th16/03/layout.json

产物：
    bases/th16/07/base.png           （原始画面，供标注/检测用）
    bases/th16/07/layout_draft.json  （grid=44 + note 里带 quad；可被 tools/annotate 直接预填/编辑）
    out/import/07_grid.png           （标定可视化，人工核验用）
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def read_image(path):
    import cv2
    data = np.fromfile(path, np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if img is None:
        raise SystemExit("无法读取图片: " + path)
    return img


def grab_screen(serial=None):
    """通过 ADB 从 LDPlayer 截一帧。"""
    from clashlab.adb import Adb
    from clashlab.config import Config
    cfg = Config().resolved()
    adb = Adb(cfg.adb, serial or cfg.serial)
    adb.ensure_device()
    frame, ms, nbytes = adb.screencap()
    print("screencap: %.1f ms, %d bytes, shape=%s" % (ms, nbytes, frame.shape))
    return frame


def main(argv=None):
    ap = argparse.ArgumentParser(description="import a CoC layout from the game screen")
    ap.add_argument("--th", type=int, default=16)
    ap.add_argument("--id", required=True, help="新阵编号，如 07")
    ap.add_argument("--from-file", default=None, help="已有截图（不截屏）")
    ap.add_argument("--serial", default=None, help="ADB serial（默认取配置）")
    ap.add_argument("--copy-from", default=None, help="用已有 layout.json 预填建筑（草稿）")
    ap.add_argument("--out-base", default=None, help="输出目录（默认 bases/th<TH>/<id>/）")
    ap.add_argument("--force", action="store_true", help="标定面积可疑时仍继续")
    a = ap.parse_args(argv)

    import cv2
    from clashlab import calib as calib_mod

    if a.from_file:
        frame = read_image(a.from_file)
        print("image:", a.from_file, frame.shape)
    else:
        frame = grab_screen(a.serial)

    calib, meta = calib_mod.detect_village_quad(frame, grid_n=44)
    # 兜底：草地检测失败时用四角回归模型（存在 checkpoint 才用）
    if calib is None:
        try:
            from clashlab import quad_model as _qm
            _m = _qm.load_model()
            _q = _m.predict(frame)
            calib = calib_mod.Calib.from_quad(__import__("numpy").array(_q, dtype=__import__("numpy").float32), n=44)
            meta = {"method": "quad-model", "quad": [[float(x), float(y)] for x, y in _q]}
            print("草地检测失败，使用四角模型兜底")
        except Exception as _e:
            print("四角模型兜底不可用：%s" % str(_e)[:80])
    if calib is None:
        print("自动标定失败:", json.dumps(meta, ensure_ascii=False))
        raise SystemExit("未检测到草地/边界，请换一张画面更完整的截图，或用 --from-file 手动提供")
    quad = [list(map(float, p)) for p in meta.get("quad", [])] if meta.get("quad") else None
    if quad is None:
        quad = [list(map(float, calib.tile_to_px(x, y))) for x, y in ((0, 0), (44, 0), (44, 44), (0, 44))]
    # 标定合理性检查：四边形面积占画面比例（游戏内村庄一般 30%~90%）
    def _area(q):
        s = 0.0
        for i in range(4):
            x1, y1 = q[i]
            x2, y2 = q[(i + 1) % 4]
            s += x1 * y2 - x2 * y1
        return abs(s) / 2.0
    ratio = _area(quad) / float(frame.shape[0] * frame.shape[1])
    calib_ok = 0.10 <= ratio <= 0.95
    print("calib method=%s reproj=%s area_ratio=%.3f calib_ok=%s" % (
        meta.get("method"), round(float(calib.reproj_error()), 6), ratio, calib_ok))
    print("quad=%s" % ([[round(v, 1) for v in p] for p in quad],))
    if not calib_ok and not a.force:
        print("WARN: 标定四边形只占画面 %.1f%%，可能截的不是游戏内村庄画面；确认无误可加 --force 继续" % (ratio * 100))

    out_dir = os.path.abspath(a.out_base or os.path.join(ROOT, "bases", "th%d" % a.th, a.id))
    os.makedirs(out_dir, exist_ok=True)
    base_png = os.path.join(out_dir, "base.png")
    cv2.imencode(".png", frame)[1].tofile(base_png)

    buildings = []
    if a.copy_from and os.path.exists(a.copy_from):
        src = json.load(open(a.copy_from, encoding="utf-8"))
        buildings = src.get("buildings") or []
        print("预填建筑:", len(buildings), "from", a.copy_from)
    walls = []

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    note = ("TH%d imported %s quad=%s reproj_error=%.6f method=%s；"
            "建筑/墙为草稿，请用 tools/annotate 校正") % (
        a.th, now, json.dumps([[round(v, 1) for v in p] for p in quad]), float(calib.reproj_error()),
        meta.get("method"))
    layout = {"name": "th%d_%s_imported" % (a.th, a.id), "grid": 44, "note": note,
              "buildings": buildings, "walls": walls,
              "meta": {"calib_ok": bool(calib_ok), "area_ratio": round(ratio, 3)}}
    lay_path = os.path.join(out_dir, "layout_draft.json")
    json.dump(layout, open(lay_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    grid_dir = os.path.join(ROOT, "out", "import")
    os.makedirs(grid_dir, exist_ok=True)
    grid_png = os.path.join(grid_dir, "%s_grid.png" % a.id)
    vis = calib_mod.draw_grid(frame.copy(), calib, step=2)
    cv2.imencode(".png", vis)[1].tofile(grid_png)

    print(json.dumps({"base": base_png, "layout_draft": lay_path, "grid_check": grid_png,
                      "buildings": len(buildings), "calib_ok": bool(calib_ok),
                      "quad": [[round(v, 1) for v in p] for p in quad]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
