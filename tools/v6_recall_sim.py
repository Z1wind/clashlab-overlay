# -*- coding: utf-8 -*-
"""v6 降采样识别率模拟（单尺度 NCC，禁止多尺度金字塔）。
每档单独建模板、单独 NCC；判据: peak>0.75 & ratio>1.5 认出; <0.6 认不出; 中间勉强。
纯离线：只读 v6_stitched_base.png，写 out/overlay/v6_recall_sim.png。
"""
import cv2, numpy as np, os, json

ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
SRC = os.path.join(ROOT, "out", "overlay", "v6_stitched_base.png")
OUT = os.path.join(ROOT, "out", "overlay", "v6_recall_sim.png")

# --- 人工读点（80px 基准图坐标，单位 px；label 为图中实际可见结构的最佳辨识）---
# (cx, cy, label, requested_name)
ROIS = [
    (560, 2200, "A", "金堆(金仓) / 金仓"),
    (3200, 750, "B", "熔岩塔(代法师塔) / 法师塔*"),
    (2500, 1900, "C", "蓝旋翼机(防空候选) / 防空塔"),
    (430, 1950, "D", "散弹(代鹰炮) / 鹰炮*"),
    (2100, 1050, "E", "黑炮攻城机(代大本营) / 大本营*"),
]

LEVELS = [("80", 80/80.0), ("59", 59/80.0), ("24.4", 24.4/80.0)]
HALF = 110          # 80px 档模板半宽(约2.75格)
SHIFT = 10          # 80px 档平移量，按档等比
PEAK_OK, RATIO_OK, PEAK_BAD = 0.75, 1.5, 0.60


def imread(path):
    return cv2.imdecode(np.fromfile(path, np.uint8), cv2.IMREAD_COLOR)


def mask_seams(img):
    """黑缝(近黑)填中性灰，避免 NCC 在黑带上出相关。"""
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    m = (g < 40)
    out = img.copy()
    out[m] = (128, 128, 128)
    return out


def ncc_search(gray, tpl, sup_r):
    res = cv2.matchTemplate(gray, tpl, cv2.TM_CCOEFF_NORMED)
    # 主峰
    _, peak, _, loc = cv2.minMaxLoc(res)
    # 抑制主峰邻域后取次峰
    r = res.copy()
    x0, y0 = max(0, loc[0]-sup_r), max(0, loc[1]-sup_r)
    x1, y1 = min(r.shape[1], loc[0]+sup_r+1), min(r.shape[0], loc[1]+sup_r+1)
    r[y0:y1, x0:x1] = -1
    _, second, _, _ = cv2.minMaxLoc(r)
    return float(peak), float(second), loc


def main():
    base = imread(SRC)
    H, W = base.shape[:2]
    base = mask_seams(base)
    panels = []
    rows = []
    for name, s in LEVELS:
        nw, nh = max(1, round(W*s)), max(1, round(H*s))
        lvl = cv2.resize(base, (nw, nh), interpolation=cv2.INTER_AREA)
        gray = cv2.cvtColor(lvl, cv2.COLOR_BGR2GRAY)
        half = max(16, round(HALF*s))
        shift = SHIFT*s
        for (cx, cy, tag, desc) in ROIS:
            X, Y = round(cx*s), round(cy*s)
            h, w = half*2, half*2
            samples = [(X, Y), (round(X-shift), Y), (round(X+shift), Y)]
            peaks, ratios, secs, locs = [], [], [], []
            for sx, sy in samples:
                x0, y0 = sx-half, sy-half
                if x0 < 0 or y0 < 0 or x0+w > nw or y0+h > nh:
                    peaks.append(-1); ratios.append(-1); secs.append(-1); continue
                tpl = gray[y0:y0+h, x0:x0+w]
                pk, sec, loc = ncc_search(gray, tpl, half)
                peaks.append(pk); secs.append(sec); ratios.append(pk/sec if sec > 0 else 9.9)
                locs.append(loc)
            best = int(np.argmax(peaks))
            peak = peaks[best]
            ratio = ratios[best]
            sec = secs[best]
            if peak > PEAK_OK and ratio > RATIO_OK:
                verdict, color = "认出", (0, 200, 0)
            elif peak < PEAK_BAD:
                verdict, color = "认不出", (0, 0, 220)
            else:
                verdict, color = "勉强", (0, 210, 230)
            rows.append(dict(level=name, tag=tag, desc=desc,
                             peak=round(peak, 3), sec=round(sec, 3),
                             ratio=round(ratio, 2), verdict=verdict))
            # 画框（当前档坐标），ASCII 标签避免字体豆腐块
            cv2.rectangle(lvl, (X-half, Y-half), (X+half, Y+half), color, 3)
            cv2.putText(lvl, f"{tag} p{peak:.2f}/r{ratio:.2f}",
                        (X-half, Y-half-8), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        # 面板缩放到统一高 600
        ph = 600
        pw = round(nw*ph/nh)
        panel = cv2.resize(lvl, (pw, ph), interpolation=cv2.INTER_AREA)
        n_hit = sum(r["verdict"] == "认出" for r in rows if r["level"] == name)
        cv2.putText(panel, f"LEVEL {name} px/tile  hit {n_hit}/5", (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
        panels.append(panel)

    Hh = max(p.shape[0] for p in panels)
    total_w = sum(p.shape[1] for p in panels)+20*len(panels)+10
    canv = np.full((Hh+60, total_w, 3), 30, np.uint8)
    x = 10
    for p in panels:
        canv[0:p.shape[0], x:x+p.shape[1]] = p
        x += p.shape[1]+20
    # 图例
    ly = Hh+15
    cv2.rectangle(canv, (20, ly), (50, ly+25), (0, 200, 0), -1)
    cv2.putText(canv, "hit peak>0.75 & ratio>1.5", (60, ly+20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 0), 2)
    cv2.rectangle(canv, (430, ly), (460, ly+25), (0, 210, 230), -1)
    cv2.putText(canv, "marginal", (470, ly+20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 210, 230), 2)
    cv2.rectangle(canv, (640, ly), (670, ly+25), (0, 0, 220), -1)
    cv2.putText(canv, "miss peak<0.6", (680, ly+20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 220), 2)
    cv2.imencode(".png", canv)[1].tofile(OUT)

    print(json.dumps(rows, ensure_ascii=False, indent=1))
    for name, _ in LEVELS:
        sub = [r for r in rows if r["level"] == name]
        n_hit = sum(r["verdict"] == "认出" for r in sub)
        n_miss = sum(r["verdict"] == "认不出" for r in sub)
        print(f"{name}: hit {n_hit}/5 miss {n_miss}/5 marginal {5-n_hit-n_miss}/5")


if __name__ == "__main__":
    main()
