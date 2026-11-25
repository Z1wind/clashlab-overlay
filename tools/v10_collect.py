# -*- coding: utf-8 -*-
# v10_collect.py — 全阵采集驱动：status / drag DIR / lock DIR / shot NAME / report
# 全部为 drag（press-move-release），无 tap；锚点避开右侧资源轨与底部按钮。
import sys, os, time, json, cv2, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v10_lib import *

# 方向 → drag.sh 起止（屏坐标 1280x720；锚点均在中部空地）
DRAG = {
    "N": (640, 150, 640, 540),
    "S": (640, 470, 640, 130),
    "E": (950, 300, 550, 300),
    "W": (330, 300, 730, 300),
}

def do_drag(d, steps=24):
    x0, y0, x1, y1 = DRAG[d]
    sh(["shell", "sh", "/data/local/tmp/drag.sh", str(x0), str(y0), str(x1), str(y1), str(steps)])
    time.sleep(1.6)

def cmd_status():
    im = grab()
    r = tile_px_of(im)
    ref = cv2.imdecode(np.fromfile(os.path.join(ROOT, "out", "overlay", "ladder", "zoom_L0.png"), dtype=np.uint8), cv2.IMREAD_COLOR)
    (sx, sy), nin, ng = orb_shift(trim(im), trim(ref)) if ref.shape[:2] == im.shape[:2] else (None, 0, 0)
    # 参考帧同样裁口
    (sx, sy), nin, ng = orb_shift(trim(im), trim(ref))
    print("tile_px:", json.dumps(r["criteria"], ensure_ascii=False), "est=", r["estimate"], "consensus=", r["consensus"])
    print("ORB vs L0 ref: inl=", nin, "good=", ng, "shift=", (sx, sy))
    print("client:", json.dumps(client_rect(), ensure_ascii=False))

def cmd_lock(d, maxiter=12):
    prev = trim(grab())
    locks = 0
    for i in range(maxiter):
        do_drag(d)
        cur = trim(grab())
        (sx, sy), nin, ng = orb_shift(prev, cur)
        m = mad(prev, cur)
        print(f"lock {d} i{i}: shift=({sx},{sy}) inl={nin}/{ng} MAD={m:.2f}")
        if (sx is None or (abs(sx) < 8 and abs(sy) < 8)) and m < 1.0:
            locks += 1
            if locks >= 2:
                print(f"LOCKED {d}")
                return True
        else:
            locks = 0
        prev = cur
    print(f"NOT LOCKED {d}")
    return False

def cmd_shot(name):
    log = load_log()
    im = grab()
    rawp = os.path.join(RAW, name + ".png")
    save_png(im, rawp)
    t = trim(im)
    blockp = os.path.join(FULL, name + ".png")
    save_png(t, blockp)
    r = tile_px_of(im)
    # vs 上一块
    shift = None; nin = 0; ng = 0
    if log["blocks"]:
        prevp = os.path.join(FULL, log["blocks"][-1]["file"])
        prev = cv2.imdecode(np.fromfile(prevp, dtype=np.uint8), cv2.IMREAD_COLOR)
        shift, nin, ng = orb_shift(prev, t)
    entry = {
        "file": name + ".png", "raw": os.path.relpath(rawp, FULL),
        "trim": list(TRIM),
        "shift_vs_prev": [round(shift[0], 2), round(shift[1], 2)] if shift else None,
        "inl": nin, "good": ng,
        "tile_px": r["criteria"], "tile_px_est": r["estimate"], "consensus": r["consensus"],
        "client": client_rect(),
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    log["blocks"].append(entry)
    save_log(log)
    print(f"shot {name}: shift={shift} inl={nin}/{ng} tile_px={r['estimate']}")

def cmd_move(d, px):
    px = float(px)
    cx, cy = 640, 300
    if d == "N":
        x0, y0, x1, y1 = cx, cy, cx, cy - px
    elif d == "S":
        x0, y0, x1, y1 = cx, cy, cx, cy + px
    elif d == "E":
        x0, y0, x1, y1 = cx, cy, cx - px, cy
    elif d == "W":
        x0, y0, x1, y1 = cx, cy, cx + px, cy
    else:
        return
    prev = trim(grab())
    sh(["shell", "sh", "/data/local/tmp/drag.sh", str(int(x0)), str(int(y0)), str(int(x1)), str(int(y1)), "12"])
    time.sleep(1.4)
    cur = trim(grab())
    shift, nin, ng = orb_shift(prev, cur)
    print(f"move {d} {px}: shift=({shift[0]:.1f},{shift[1]:.1f}) inl={nin}/{ng}" if shift else f"move {d}: no match {nin}/{ng}")

def cmd_test(d):
    prev = trim(grab())
    do_drag(d)
    cur = trim(grab())
    shift, nin, ng = orb_shift(prev, cur)
    print(f"test {d}: shift=({shift[0]:.1f},{shift[1]:.1f}) inl={nin}/{ng}" if shift else f"test {d}: no match inl={nin}/{ng}")

REF = None
def get_ref():
    global REF
    if REF is None:
        REF = cv2.imdecode(np.fromfile(os.path.join(ROOT, "out", "overlay", "ladder", "zoom_L0.png"), dtype=np.uint8), cv2.IMREAD_COLOR)
    return REF

def cmd_recenter(maxiter=15):
    ref = trim(get_ref())
    for i in range(maxiter):
        cur = trim(grab())
        shift, nin, ng = orb_shift(cur, ref)
        print(f"recenter {i}: shift=({shift[0]:.1f},{shift[1]:.1f}) inl={nin}/{ng}" if shift else f"recenter {i}: no match {nin}/{ng}")
        if shift is None:
            break
        sx, sy = shift
        if abs(sx) < 20 and abs(sy) < 20:
            print("CENTERED"); return True
        if sx < -20:
            do_drag("W")
        elif sx > 20:
            do_drag("E")
        if sy > 20:
            do_drag("S")
        elif sy < -20:
            do_drag("N")
        time.sleep(0.8)
    print("recenter done")
    return False

def cmd_report():
    log = load_log()
    for b in log["blocks"]:
        print(b["file"], "shift=", b["shift_vs_prev"], "inl=", b["inl"], "tile=", b["tile_px_est"])

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "status":
        cmd_status()
    elif cmd == "drag":
        do_drag(sys.argv[2]); time.sleep(0.5)
        im = grab(); print("dragged", sys.argv[2])
    elif cmd == "lock":
        cmd_lock(sys.argv[2])
    elif cmd == "test":
        cmd_test(sys.argv[2])
    elif cmd == "move":
        cmd_move(sys.argv[2], sys.argv[3])
    elif cmd == "recenter":
        cmd_recenter()
    elif cmd == "shot":
        cmd_shot(sys.argv[2])
    elif cmd == "report":
        cmd_report()
