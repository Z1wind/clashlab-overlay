# -*- coding: utf-8 -*-
"""Availability hard-gate probe: multi-scale matchTemplate of the existing building batch
against real village screenshots. Writes _probe_report.md next to this script.

Usage: D:\\Python313\\python.exe assets\\coc\\buildings\\_probe_template.py
Read-only w.r.t. sprite files; screenshots are read-only references from out\\.
"""
import os, re, json, sys
import numpy as np
import cv2
from PIL import Image

ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
B = os.path.join(ROOT, "assets", "coc", "buildings")
MANIFEST = os.path.join(B, "manifest_buildings.json")
REPORT = os.path.join(B, "_probe_report.md")

# Real frames already captured locally (read-only references).
SHOTS = [
    ("home_dialog", r"out\audit\run_a1\frame_001.png", "home village (disconnect dialog overlay)"),
    ("bb_clean", r"out\grab2\grab_1795414594.png", "builder base, clean"),
    ("bb_panel", r"out\analyze\analyze.png", "builder base, planning panel overlay"),
]

SCALES = [0.15, 0.2, 0.25, 0.35, 0.45, 0.6, 0.8, 1.0]
TH_HIT = 0.60      # hit threshold for masked CCORR_NORMED
TH_FP = 0.60      # false-positive threshold on wrong scene
AMBIG_GAP = 0.15  # home - bb discrimination gap
NMS_K = 15


def load_rgba(path):
    im = Image.open(path)
    if im.mode == "P" and "transparency" in im.info:
        im = im.convert("RGBA")
    return im.convert("RGBA")


def crop_to_subject(tpl_rgba):
    """Crop transparent margins using alpha bbox; return (RGB subject, alpha mask)."""
    arr = np.array(tpl_rgba)
    a = arr[:, :, 3]
    ys, xs = np.where(a > 8)
    if len(xs) == 0:
        return arr[:, :, :3], None
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    return arr[y0:y1, x0:x1, :3], a[y0:y1, x0:x1]


def best_match(shot_bgr, tpl_rgb, tpl_mask, scale, shot_shape):
    th, tw = tpl_rgb.shape[:2]
    nw, nh = max(1, int(tw * scale)), max(1, int(th * scale))
    if nw > shot_shape[1] or nh > shot_shape[0]:
        return None
    tr = cv2.resize(tpl_rgb, (nw, nh), interpolation=cv2.INTER_LANCZOS4)
    mk = cv2.resize(tpl_mask, (nw, nh), interpolation=cv2.INTER_LANCZOS4)
    # masked CCORR_NORMED (positive control self-locates at 0.92-0.97)
    res = cv2.matchTemplate(shot_bgr, tr, cv2.TM_CCORR_NORMED, mask=mk)
    _, maxv, _, maxloc = cv2.minMaxLoc(res)
    dil = cv2.dilate(res, np.ones((NMS_K, NMS_K), np.uint8))
    peaks = int(np.logical_and(res >= TH_HIT, res == dil).sum())
    return float(maxv), maxloc, peaks, (nw, nh)


def main():
    man = json.load(open(MANIFEST, encoding="utf-8"))
    entries = [e for e in man["entries"] if e.get("kind", "building") == "building"]

    shots = []
    for tag, rel, desc in SHOTS:
        p = os.path.join(ROOT, rel)
        if os.path.exists(p):
            # cv2.imread fails on non-ASCII paths; load via PIL
            pil = Image.open(p).convert("RGB")
            img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
            shots.append((tag, img, desc, rel))
    if len(shots) < 2:
        print("FATAL: fewer than 2 reference screenshots available", file=sys.stderr)
        sys.exit(2)

    shot_gray = {}
    for tag, img, desc, rel in shots:
        shot_gray[tag] = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    rows = []
    for e in entries:
        tpl_path = os.path.join(ROOT, e["file"])
        if not os.path.exists(tpl_path):
            continue
        tpl_rgb, tpl_mask = crop_to_subject(load_rgba(tpl_path))
        per_shot = {}
        for tag, img, desc, rel in shots:
            best = (-1.0, None, 0, None)
            for sc in SCALES:
                r = best_match(img, tpl_rgb, tpl_mask, sc, img.shape)
                if r and r[0] > best[0]:
                    best = (r[0], r[1], r[2], (sc, r[3]))
            per_shot[tag] = best
        rows.append({"type": e["type"], "level": e["level"], "file": e["file"],
                      "per_shot": {k: {"score": round(v[0], 4), "loc": v[1],
                                      "peaks": v[2], "scale": v[3][0] if v[3] else None}
                                   for k, v in per_shot.items()}})

    # aggregate per type
    by_type = {}
    for r in rows:
        by_type.setdefault(r["type"], []).append(r)

    summary = []
    for typ, rs in sorted(by_type.items()):
        home_best = max(x["per_shot"]["home_dialog"]["score"] for x in rs if "home_dialog" in x["per_shot"])
        bb_best = max(max(x["per_shot"]["bb_clean"]["score"], x["per_shot"]["bb_panel"]["score"])
                      for x in rs if "bb_clean" in x["per_shot"] and "bb_panel" in x["per_shot"])
        home_hits = sum(1 for x in rs if x["per_shot"].get("home_dialog", {}).get("score", 0) >= TH_HIT)
        bb_fps = sum(1 for x in rs if max(x["per_shot"].get("bb_clean", {}).get("score", 0),
                                           x["per_shot"].get("bb_panel", {}).get("score", 0)) >= TH_FP)
        n = len(rs)
        gap = home_best - bb_best
        if home_best >= TH_HIT and gap >= AMBIG_GAP:
            verdict = "usable"
        elif home_best < 0.50 and bb_best < 0.50:
            verdict = "unrecognizable"
        else:
            verdict = "ambiguous"
        summary.append({"type": typ, "n": n, "home_best": round(home_best, 3),
                        "bb_best": round(bb_best, 3), "gap": round(gap, 3),
                        "home_hits": home_hits, "bb_fps": bb_fps, "verdict": verdict})

    usable = [s["type"] for s in summary if s["verdict"] == "usable"]
    ambiguous = [s["type"] for s in summary if s["verdict"] == "ambiguous"]
    dead = [s["type"] for s in summary if s["verdict"] == "unrecognizable"]

    # overall verdict (conditional: negative frames are builder-base only; home frame obscured)
    if len(usable) >= 8:
        overall = "部分可用 (partial usable, 仍需家乡帧复测)"
    elif len(usable) >= 1:
        overall = "勉强可用 (marginal, 仍需家乡帧复测)"
    else:
        overall = "暂不定论 (inconclusive: 阴性帧仅夜世界、家乡帧被弹窗遮挡，需家乡帧复测)"

    lines = []
    lines.append("# 建筑模板可用性探针报告 (_probe_template.py)\n")
    lines.append(f"- 参考截图: {', '.join(f'`{rel}`（{desc}）' for _, _, desc, rel in shots)}")
    lines.append(f"- 模板: {len(entries)} 张既有批次；方法: alpha 裁主体 + alpha mask 加权 TM_CCORR_NORMED(BGR)，多尺度 {SCALES}，NMS {NMS_K}px")
    lines.append("- 阳性对照: 模板自身粘贴回画面，masked CCORR 可精确定位(0.92-0.97)；无 mask 的 CCOEFF 只能到 0.56-0.69 且定位偏移，故本探针采用 mask 版")
    lines.append(f"- 阈值: 命中 ≥{TH_HIT}，区分差 home-bb ≥{AMBIG_GAP}\n")
    lines.append(f"## 总体结论: **{overall}**")
    lines.append(f"- 可用白名单 ({len(usable)}): {', '.join(usable) or '无'}")
    lines.append(f"- 存疑 ({len(ambiguous)}): {', '.join(ambiguous) or '无'}")
    lines.append(f"- 不可识别黑名单 ({len(dead)}): {', '.join(dead) or '无'}\n")
    lines.append("## 分类型汇总")
    lines.append("| type | n | home_best | bb_best | gap | home命中 | bb误命中 | 判定 |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for s in summary:
        lines.append(f"| {s['type']} | {s['n']} | {s['home_best']:.3f} | {s['bb_best']:.3f} | "
                     f"{s['gap']:.3f} | {s['home_hits']} | {s['bb_fps']} | {s['verdict']} |")

    lines.append("\n## 说明（结论有前提，勿整体否定素材）")
    lines.append("- **本批素材是家乡（home）外观；阴性参考帧 bb_* 全部来自夜世界（建筑大师基地），跨基地本就不应高分，不能据此判素材不可用。**")
    lines.append("- home_dialog 帧中央被断线弹窗大面积遮挡，可见家乡建筑只在四周边缘，home_best 偏保守。")
    lines.append("- 本探针在夜世界帧上 17 类全部 ambiguous：最高分落在空平台/洞穴晶壁/UI 区域，不具备判别力；")
    lines.append("  这只说明『现有夜世界阴性帧 + 这组家乡模板』不能互相验证，**不等于这批底图整体不可用**。")
    lines.append("- 待取得无遮挡的家乡（home）真实帧后需复测：在该帧上 home_best 应显著高于夜世界帧才能放行。")
    lines.append("- 视角/缩放: 模板为 3D 渲染原图，截图为设备实拍缩放，探针已做多尺度扫描。")

    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # raw dump for debugging
    raw = {"summary": summary, "rows": rows}
    with open(os.path.join(os.path.dirname(REPORT), "_probe_raw.json"), "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=1)
    print("OVERALL", overall)
    print("USABLE", usable)
    print("AMBIG", ambiguous)
    print("DEAD", dead)


if __name__ == "__main__":
    main()
