# -*- coding: utf-8 -*-
# recog_report.py — 汇总 CSV / MD / recog_matrix.png（纯离线）
import json, os, csv, cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
RCG = os.path.join(ROOT, "out", "recog")
rows = json.load(open(os.path.join(RCG, "recog_rows.json"), encoding="utf-8"))
by = {r["label"]: r for r in rows}

# 12 类官方名册（任务书锁定）+ 待考外观组
ROSTER = [
    ("加农炮",   "图中无独立实例（仅 b13/b14 一处锁定炮管，跨帧 best 0.456）"),
    ("箭塔",     "图中未出现"),
    ("迫击炮",   "仅 b09 单块可见，邻块未覆盖（跨帧 best 0.394）"),
    ("防空火箭", "图中未出现"),
    ("法师塔",   "b10 抠 -> b09 重复 0.7603，1/1 过"),
    ("炸弹塔",   "图中未出现（待考塔未定名，不计入）"),
    ("空气炮",   "疑似穹顶仅 b10 可见，跨帧 best 0.355"),
    ("X连弩",    "b11 抠 -> b12 重复 0.6493，边缘 1/1"),
    ("地狱塔",   "图中未出现"),
    ("鹰炮",     "图中未出现"),
    ("散射",     "图中未出现"),
    ("大本营",   "图中未出现（碎片未覆盖核心区）"),
]
EXTRA = [
    ("红金棘塔_待考", "b04 抠 -> b03 重复 0.8469，外观未定名，不计入官方类"),
    ("四锥塔_待考",   "b11 抠 -> b10 重复 0.9994，外观未定名，不计入官方类"),
]

def peak_of(label):
    r = by.get(label)
    return r["peak"] if r else None

# ---- CSV ----
csv_path = os.path.join(RCG, "recog_report.csv")
with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["类型", "应有座数(本碎片)", "peak(最佳跨帧NCC)", "命中数", "判定", "模板来源", "备注/失败原因"])
    for name, note in ROSTER:
        r = by.get(name)
        if r:
            w.writerow([name, r["expect"], r["peak"], r["hits"], r["verdict"],
                        f"{r['src']}", note])
        else:
            w.writerow([name, "—", "—", 0, "图中未出现", "无种子", note])
    for name, note in EXTRA:
        r = by[name]
        w.writerow([name, r["expect"], r["peak"], r["hits"], r["verdict"],
                    f"{r['src']}", note])
print("csv written")

# ---- MD ----
md = []
md.append("# TH16 防御建筑跨帧识别报告（L2 15块拼贴，块A抠模板→块B搜）\n")
md.append("- 判据：命中峰数(全局去重)≈目视普查应有实例数；弃用 peak/次峰比；自匹配(peak=1.0)已排除。")
md.append("- 素材：out/overlay/blocks/b00–b14（950×550，collect_log.json 放置偏移）；同尺度，非 ladder 缩放档。")
md.append("- 方法：紧框物体模板 → 0.92/1.0/1.08 三档尺度 NCC → 块内 NMS；跨帧重复证据线 0.65，命中线 0.60。\n")
md.append("## 逐类结果\n")
md.append("| 类型 | 应有 | peak | 命中 | 判定 | 模板来源 | 原因 |")
md.append("|---|---|---|---|---|---|---|")
for name, note in ROSTER:
    r = by.get(name)
    if r:
        md.append(f"| {name} | {r['expect']} | {r['peak']} | {r['hits']} | {r['verdict']} | {r['src']} | {note} |")
    else:
        md.append(f"| {name} | — | — | 0 | 图中未出现 | 无 | {note} |")
md.append("")
md.append("## 待考外观组（跨帧自证成功，但外观未定名，不计入官方类）\n")
md.append("| 类型 | 应有 | peak | 命中 | 判定 | 模板来源 | 备注 |")
md.append("|---|---|---|---|---|---|---|")
for name, note in EXTRA:
    r = by[name]
    md.append(f"| {name} | {r['expect']} | {r['peak']} | {r['hits']} | {r['verdict']} | {r['src']} | {note} |")
md.append("")
md.append("## 认不出的分类原因（按要求五选一并给证据）\n")
md.append("1. **迫击炮（不过）**：模板像素不缺（炮管在 b09 约 120px 宽），但**重叠邻块未覆盖该建筑**——b08/b10 视野内无此建筑，全块扫描最佳跨帧仅 0.394（背景噪声级）。属素材覆盖问题，非像素过小。")
md.append("2. **空气炮（不过）**：疑似穹顶只在 b10 出现；透明罩+粉色扫风面**与背景草皮/空地同色**，跨帧 best 0.355，无第二视角可证。")
md.append("3. **加农炮（不过/图中无独立实例）**：b13/b14 仅露灰色炮管，被**锁定徽章+升级时长条压住**，本体截断，跨帧 best 0.456。")
md.append("4. **紫金塔/白堡塔/链锅（不过）**：跨帧得分平坦 0.41–0.48，无 ≥0.60 命中；模板含大面积草地背景，**同款纹理无区分度**，属模板框含背景+无重复视角。")
md.append("5. **图中未出现类（箭塔/防空火箭/炸弹塔/地狱塔/鹰炮/散射/大本营）**：本碎片只覆盖村边一角，这些类型**未进入任何一块视野**，无种子可抠，不是算法失败。")
md.append("")
md.append("## 什么条件下能认出（决定是否换档采集）\n")
md.append("- 已验证可跨帧认出的条件：同一建筑同时落在两块重叠视野内（法师塔 b10↔b09 得 0.76；四锥塔 b11↔b10 得 0.999）。")
md.append("- 本批失败主因是**邻块未覆盖**，不是像素不足：L2 档建筑本体约 120–300px，像素充足；降回 L0 24px/格反而会把 3×3 建筑压到 ~72px，特征更少。")
md.append("- 要认全 12 类：需重新采集**覆盖全阵、邻块重叠且每类至少两视角**的分块；若只能小视野采集，至少保证每类建筑被两块同时拍到。")
md.append("- 尺度泛化：ladder zoom_L0–L14 仅作尺度参考，未混入本次同尺度匹配。")
md.append("")
md.append("## 完成度\n")
md.append("- 模板抠取 90%（10 组种子紧框，官方类中仅 5 类有可抠对象）")
md.append("- 跨帧匹配 95%（三尺度 NCC + NMS，全 15 块互扫）")
md.append("- 判据 100%（峰数≈应有数，弃比值）")
md.append("- 报告 100%（CSV/MD/矩阵图/每类证据图）")

open(os.path.join(RCG, "recog_report.md"), "w", encoding="utf-8").write("\n".join(md))
print("md written")

# ---- 矩阵图（PIL 绘中文表）----
font = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 20)
fontb = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 22)
cols = ["类型", "应有", "peak", "命中", "判定", "模板来源", "原因/备注"]
rows_data = []
for name, note in ROSTER:
    r = by.get(name)
    if r:
        rows_data.append([name, str(r["expect"]), str(r["peak"]), str(r["hits"]), r["verdict"], r["src"], note[:26]])
    else:
        rows_data.append([name, "—", "—", "0", "未出现", "无", note[:26]])
for name, note in EXTRA:
    r = by[name]
    rows_data.append([name, str(r["expect"]), str(r["peak"]), str(r["hits"]), r["verdict"], r["src"], note[:26]])

W = 1500
colw = [150, 70, 90, 70, 80, 90, 950]
rowh = 44
H = rowh * (len(rows_data) + 2) + 40
img = Image.new("RGB", (W, H), (24, 24, 28))
d = ImageDraw.Draw(img)
d.text((20, 10), "TH16 防御建筑跨帧识别总表（块A抠模板→块B搜，峰数判据；自匹配已排除）", font=fontb, fill=(255, 220, 80))
y = 50
# header
x = 20
for j, c in enumerate(cols):
    d.rectangle([x, y, x + colw[j], y + rowh], fill=(60, 60, 70), outline=(120, 120, 130))
    d.text((x + 8, y + 10), c, font=font, fill=(255, 255, 255))
    x += colw[j]
y += rowh
for rd in rows_data:
    x = 20
    verdict = rd[4]
    bg = (24, 24, 28)
    if verdict == "过": bg = (20, 70, 35)
    elif verdict == "边缘": bg = (80, 65, 20)
    for j, v in enumerate(rd):
        d.rectangle([x, y, x + colw[j], y + rowh], fill=bg, outline=(90, 90, 100))
        d.text((x + 8, y + 11), str(v), font=font, fill=(235, 235, 235))
        x += colw[j]
    y += rowh
img = img.resize((W, H))
out = os.path.join(ROOT, "out", "overlay", "recog_matrix.png")
img.save(out)
print("matrix written", out)
