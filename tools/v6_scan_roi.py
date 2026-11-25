# -*- coding: utf-8 -*-
"""扫描 80px 档候选正样本：单尺度自NCC，报 second-best 与 ratio，挑独特、分散的锚点。
只读 v6_stitched_base.png；写 tools/base_out/roi_scan.png。"""
import cv2, numpy as np, os, json

ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
SRC = os.path.join(ROOT, "out", "overlay", "v6_stitched_base.png")
OUT = os.path.join(ROOT, "tools", "base_out", "roi_scan.png")
HALF = 110
STEP = 160


def imread(p):
    return cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)


def main():
    img = imread(SRC)
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    g[(g < 40)] = 128
    H, W = g.shape
    cands = []
    for cy in range(HALF+30, H-HALF-30, STEP):
        for cx in range(HALF+30, W-HALF-30, STEP):
            # 要求模板窗内基本非黑（内容）
            win = g[cy-HALF:cy+HALF, cx-HALF:cx+HALF]
            if (win < 40).mean() > 0.25:
                continue
            tpl = win
            res = cv2.matchTemplate(g, tpl, cv2.TM_CCOEFF_NORMED)
            _, peak, _, loc = cv2.minMaxLoc(res)
            r = res.copy()
            r[max(0, loc[1]-HALF):loc[1]+HALF+1,
              max(0, loc[0]-HALF):loc[0]+HALF+1] = -1
            _, sec, _, sloc = cv2.minMaxLoc(r)
            ratio = peak/sec if sec > 0 else 9.9
            cands.append((ratio, peak, sec, cx, cy, sloc))
    cands.sort(reverse=True)
    # 贪心选分散锚点
    picked = []
    for ratio, peak, sec, cx, cy, sloc in cands:
        if all((cx-p[3])**2+(cy-p[4])**2 > 450**2 for p in picked):
            picked.append((ratio, peak, sec, cx, cy, sloc))
        if len(picked) == 8:
            break
    vis = img.copy()
    for i, (ratio, peak, sec, cx, cy, sloc) in enumerate(picked):
        cv2.rectangle(vis, (cx-HALF, cy-HALF), (cx+HALF, cy+HALF), (0, 200, 0), 3)
        cv2.putText(vis, f"#{i} r{ratio:.2f} s{sec:.2f}", (cx-HALF, cy-HALF-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 200, 0), 3)
    ov = cv2.resize(vis, (1500, round(H*1500/W)), interpolation=cv2.INTER_AREA)
    cv2.imencode(".png", ov)[1].tofile(OUT)
    for i, (ratio, peak, sec, cx, cy, sloc) in enumerate(picked):
        print(f"#{i} center=({cx},{cy}) peak={peak:.3f} sec={sec:.3f} ratio={ratio:.2f} sec_loc={sloc}")


if __name__ == "__main__":
    main()
