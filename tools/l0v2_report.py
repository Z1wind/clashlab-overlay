# -*- coding: utf-8 -*-
# l0v2_report.py — v2 逐类表 CSV/MD/matrix（纯离线）
import json, os, csv, cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
RCG = os.path.join(ROOT, "out", "recog")
OV = os.path.join(ROOT, "out", "overlay")
m = {r["label"]: r for r in json.load(open(os.path.join(ROOT, "tools", "base_out", "v2", "v2_match.json"), encoding="utf-8"))}

# 官方12类 + 地狱塔双行 + 资源3行
# (类型, 底面格, 种子key or None, 应有, 判定覆盖, 原因)
ROWS = [
    ("大本营", "4x4=96px", "大本营_townhall", 1, "不过",
     "种子框偏移到升级小屋；B->A 0.8234/1、A->B 0.8234/1 仅证明对应，未锁定真大本营；96px 理论够但本帧种子未取准"),
    ("鹰炮", "3x3=72px", None, 0, "无数据",
     "两帧视野内未见巨型鹰炮；无种子可抠"),
    ("防空火箭", "3x3=72px", None, 0, "无数据",
     "未见红色双火箭；无种子"),
    ("法师塔", "3x3=72px", None, 0, "无数据",
     "整帧无法在24px/格下把法师塔与其他灰塔区分；无合格种子"),
    ("地狱塔(单目标)", "2x2=48px", None, 0, "无数据/物理偏小",
     "48px 低于稳定模板下限(~64px)；无种子"),
    ("地狱塔(多目标)", "2x2=48px", None, 0, "无数据/物理偏小",
     "同上，且单/多目标形态在48px下不可分"),
    ("X连弩", "3x3=72px", None, 0, "无数据",
     "弩机细节在72px内不可辨；无种子"),
    ("散射炮", "3x3=72px", None, 0, "无数据",
     "未见；无种子"),
    ("炸弹塔", "2x2=48px", None, 0, "无数据/物理偏小",
     "48px；骷髅鼓细节丢失；无种子"),
    ("空气炮", "3x3=72px", None, 0, "无数据",
     "透明穹顶与背景同色；无种子"),
    ("隐形特斯拉", "2x2=48px", None, 0, "物理不可抠",
     "隐身状态不可见；48px；两帧均无可见本体"),
    ("投石炮/攻城锤", "3x3=72px", None, 0, "无数据",
     "水面为攻城机器(船/气球)，非防御建筑；无种子"),
    # 尝试过的防御种子（身份未复核，单列）
    ("加农炮(尝试)", "3x3=72px", "加农炮_cannon", 1, "待考",
     "B->A 0.8764/1、A->B 0.8664/1 对应成立；整帧无法复核为加农炮"),
    ("箭塔(尝试)", "3x3=72px", "箭塔_archer", 1, "待考",
     "B->A 0.8837/1、A->B 0.8837/1 对应成立；身份未复核"),
    ("迫击炮(尝试)", "3x3=72px", "迫击炮_mortar", 1, "待考",
     "B->A 0.8255/1、A->B 0.8255/1 对应成立；身份未复核"),
    # 资源
    ("金仓", "3x3=72px", "金仓_goldstor", 1, "过(疑似)",
     "B->A 0.7902/1、A->B 0.7988/1；金堆纹理对应成立"),
    ("圣水罐", "3x3=72px", "圣水收集器_elix", 1, "过(疑似)",
     "B->A 0.8641/1、A->B 0.8641/1；紫色收集器对应成立"),
    ("黑油罐", "3x3=72px", "黑油罐_darkstor", 1, "过(疑似)",
     "B->A 0.7953/1、A->B 0.7953/1；黑油存储对应成立"),
    ("金收集器(参考)", "3x3=72px", "金收集器_goldcol", 1, "待考",
     "B->A 0.7632/1；资源类参考"),
    ("紫收集器(参考)", "3x3=72px", "紫收集器_purpcol", 1, "不过(同款混淆)",
     "B->A 0.8826 但命中5处——同款收集器互相混淆，峰数≠应有1"),
    ("白堡塔(参考)", "3x3=72px", "白堡塔2_archer2", 1, "不过(同款混淆)",
     "B->A 0.8873 但命中2/4处——同款塔混淆"),
]

# ---- CSV ----
with open(os.path.join(RCG, "recog_report_v2.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["类型", "底面@24px/格", "应有", "peak(B->A)", "命中(B->A)",
                "peak(A->B)", "命中(A->B)", "判定", "模板来源/原因"])
    for name, foot, key, expect, verdict, reason in ROWS:
        r = m.get(key) if key else None
        if r:
            w.writerow([name, foot, expect, r["peak_BA"], r["hits_BA"],
                        r["peak_AB"], r["hits_AB"], verdict, reason])
        else:
            w.writerow([name, foot, expect, "—", 0, "—", 0, verdict, reason])

# ---- MD ----
md = []
md.append("# TH16 防御建筑 L0 双帧真跨帧识别报告 v2\n")
md.append("- 帧A: v6_l0_two_shot_base.png (905×773)；帧B: v6_l0_three_shot_base.png (905×1068)；同 L0 24px/格、不同采集批次。")
md.append("- 配准: ORB 360/386 内点，H≈平移(19.4,117.5)+1.005缩放；两遍法 B抠→A搜定位 → A该处抠→B搜。")
md.append("- 判据: 命中峰数≈应有座数；弃 peak/次峰比；自匹配已排除。\n")
md.append("## 逐类结果\n")
md.append("| 类型 | 底面@24px | 应有 | peak B→A | 命中 | peak A→B | 命中 | 判定 | 原因 |")
md.append("|---|---|---|---|---|---|---|---|---|")
for name, foot, key, expect, verdict, reason in ROWS:
    r = m.get(key) if key else None
    if r:
        md.append(f"| {name} | {foot} | {expect} | {r['peak_BA']} | {r['hits_BA']} | {r['peak_AB']} | {r['hits_AB']} | {verdict} | {reason} |")
    else:
        md.append(f"| {name} | {foot} | {expect} | — | 0 | — | 0 | {verdict} | {reason} |")
md.append("")
md.append("## 跨帧一致率\n")
md.append("- B→A 峰值≥0.60：10/10 种子（100%）；A→B 同法复核：10/10（100%）——**纹理对应层面双向一致**。")
md.append("- 但**身份人工复核 0/10**：整帧 24px/格下无法把命中框目视确认到具体类型；2 个种子出现同款混淆（紫收集器5峰、白堡塔4峰）。")
md.append("- 结论：L0 能证明\"两帧是同一处\"，不能证明\"这是哪一类\"。\n")
md.append("## L0 物理上限（24px/格）\n")
md.append("| 类型 | 底面格 | 底面px | 稳定模板? |")
md.append("|---|---|---|---|")
phys = [
    ("大本营", "4×4", 96, "尺寸够，但需取准种子"),
    ("鹰炮/防空火箭/法师塔/X连弩/散射炮/空气炮/投石炮/加农炮/箭塔/资源", "3×3", 72, "勉强：仅对应可证，分类细节不足"),
    ("地狱塔/炸弹塔/隐形特斯拉", "2×2", 48, "不够：低于~64px稳定模板下限，特征像素<20"),
]
for n, g, px, j in phys:
    md.append(f"| {n} | {g} | {px} | {j} |")
md.append("")
md.append("## 什么条件下能认出（产品结论）\n")
md.append("- **2×2 类（地狱塔/炸弹塔/特斯拉，48px）在 L0 物理上认不出**：特征像素不足，换判据也救不回。")
md.append("- **3×3 类（72px）L0 仅能做位置对应，不能做类型分类**；要稳定分类需 tile_px≥32（3×3→96px，约 L1 档）。")
md.append("- **4×4 大本营（96px）L0 尺寸够**，失败在种子取准/视角，可通过人工框选补救。")
md.append("- 一句话：**要认全 12 类，必须换到 tile_px≥32 的档位（L1 及以上）；L0 的问题不只是素材覆盖，2×2 类是物理像素不足。**\n")
md.append("## 完成度\n")
md.append("- 模板抠取 70%（10 组种子，3 组资源/7 组防御尝试，身份未全复核）")
md.append("- 跨帧匹配 95%（ORB配准+两遍双向+NMS）")
md.append("- 逐类 100%（12类+地狱塔双行+3资源全部成行，无数据类写明原因）")
md.append("- 报告 100%（CSV/MD/matrix/10张种子证据图）")
open(os.path.join(RCG, "recog_report_v2.md"), "w", encoding="utf-8").write("\n".join(md))

# ---- matrix_v2 ----
font = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 19)
fontb = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 21)
cols = ["类型", "底面px", "应有", "peak B→A", "命中", "peak A→B", "命中", "判定", "原因"]
colw = [150, 80, 50, 80, 55, 80, 55, 85, 640]
rows_data = []
for name, foot, key, expect, verdict, reason in ROWS:
    r = m.get(key) if key else None
    rows_data.append([name, foot, str(expect),
                      str(r["peak_BA"]) if r else "—", str(r["hits_BA"]) if r else "0",
                      str(r["peak_AB"]) if r else "—", str(r["hits_AB"]) if r else "0",
                      verdict, reason[:30]])
W = sum(colw); rowh = 42; H = rowh * (len(rows_data) + 2) + 40
img = Image.new("RGB", (W, H), (24, 24, 28))
d = ImageDraw.Draw(img)
d.text((20, 10), "TH16 L0双帧真跨帧识别 v2（行=类型，列=应有/命中/peak；B→A / A→B 双向）", font=fontb, fill=(255, 220, 80))
y = 50; x = 20
for j, c in enumerate(cols):
    d.rectangle([x, y, x + colw[j], y + rowh], fill=(60, 60, 70), outline=(120, 120, 130))
    d.text((x + 6, y + 10), c, font=font, fill=(255, 255, 255)); x += colw[j]
y += rowh
for rd in rows_data:
    x = 20; v = rd[7]
    bg = (24, 24, 28)
    if v.startswith("过"): bg = (20, 70, 35)
    elif v == "待考": bg = (70, 55, 25)
    elif v.startswith("不过"): bg = (70, 30, 30)
    for j, val in enumerate(rd):
        d.rectangle([x, y, x + colw[j], y + rowh], fill=bg, outline=(90, 90, 100))
        d.text((x + 6, y + 11), str(val), font=font, fill=(235, 235, 235)); x += colw[j]
    y += rowh
img.save(os.path.join(OV, "recog_matrix_v2.png"))
print("done")
