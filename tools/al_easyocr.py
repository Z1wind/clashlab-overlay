# -*- coding: utf-8 -*-
"""步骤 2：easyocr 引擎能力验证（不碰游戏，用存量截图）。

真值：
  info1.png        面板标题「12级兵营」
  tap_0_890_380.png 名称卡片「建筑工人小屋（2级）」
目标：标题/名称行能读对至少 1 张；结果写 easyocr_check.json。
"""
import json, os, sys, time
import numpy as np, cv2

BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "out", "overlay", "_auto_label")


def imread(path):
    return cv2.imdecode(np.fromfile(path, np.uint8), cv2.IMREAD_COLOR)


def main():
    t0 = time.time()
    import easyocr
    reader = easyocr.Reader(["ch_sim", "en"], gpu=False, verbose=False)
    init_sec = time.time() - t0
    cases = [
        ("info1.png", (500, 20, 800, 72), "12级兵营"),
        ("info1.png", (200, 60, 1100, 620), "面板整体"),
        ("tap_0_890_380.png", (430, 440, 860, 522), "建筑工人小屋（2级）"),
        ("state_now.png", (540, 460, 800, 505), "兵营（12级）"),
    ]
    results = []
    for fn, box, truth in cases:
        path = os.path.join(OUT, fn)
        if not os.path.exists(path):
            results.append({"file": fn, "box": box, "truth": truth, "error": "missing"})
            continue
        img = imread(path)
        x0, y0, x1, y1 = box
        reg = img[y0:y1, x0:x1]
        reg = cv2.resize(reg, (reg.shape[1] * 2, reg.shape[0] * 2), interpolation=cv2.INTER_LANCZOS4)
        t1 = time.time()
        out = reader.readtext(reg, detail=0, paragraph=False)
        dt = time.time() - t1
        results.append({"file": fn, "box": box, "truth": truth, "lines": out,
                        "sec": round(dt, 2)})
        print("%s %s -> %d lines %.2fs" % (fn, truth, len(out), dt))
    payload = {"init_seconds": round(init_sec, 2), "cases": results}
    json.dump(payload, open(os.path.join(OUT, "easyocr_check.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("init_seconds=%.1f" % init_sec)


if __name__ == "__main__":
    main()
