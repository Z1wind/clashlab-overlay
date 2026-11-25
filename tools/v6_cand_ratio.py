# -*- coding: utf-8 -*-
"""诊断：手工候选建筑中心在 80px 档的自NCC peak/sec/ratio。"""
import cv2, numpy as np, os

ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
SRC = os.path.join(ROOT, "out", "overlay", "v6_stitched_base.png")
HALF = 110

CANDS = [
    ("法师塔A", 820, 1650),
    ("法师塔B", 4150, 1900),
    ("金仓顶", 4900, 1400),
    ("金堆", 560, 2200),
    ("蓝旋翼", 2500, 1900),
    ("紫储", 2750, 1600),
    ("散弹", 430, 1950),
    ("熔岩塔", 3200, 750),
    ("黑炮", 2100, 1050),
    ("蓝龙", 300, 1400),
    ("紫柱", 1900, 400),
    ("金币堆2", 4900, 2150),
]

def main():
    img = cv2.imdecode(np.fromfile(SRC, np.uint8), cv2.IMREAD_COLOR)
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    g[g < 40] = 128
    H, W = g.shape
    for name, cx, cy in CANDS:
        x0, y0 = cx-HALF, cy-HALF
        if x0 < 0 or y0 < 0 or x0+2*HALF > W or y0+2*HALF > H:
            print(f"{name}: out"); continue
        tpl = g[y0:y0+2*HALF, x0:x0+2*HALF]
        res = cv2.matchTemplate(g, tpl, cv2.TM_CCOEFF_NORMED)
        _, peak, _, loc = cv2.minMaxLoc(res)
        r = res.copy()
        r[max(0, loc[1]-HALF):loc[1]+HALF+1, max(0, loc[0]-HALF):loc[0]+HALF+1] = -1
        _, sec, _, sloc = cv2.minMaxLoc(r)
        print(f"{name} ({cx},{cy}) peak={peak:.3f} sec={sec:.3f} ratio={peak/sec:.2f} sec_loc={sloc}")

if __name__ == "__main__":
    main()
