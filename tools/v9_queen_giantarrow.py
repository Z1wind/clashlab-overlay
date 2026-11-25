# -*- coding: utf-8 -*-
"""
v9_queen_giantarrow.py — TH16 女王三段走位 + 穿云箭弹道 战术图（纯离线程序化叠加，修订版）

修订要点（用户打回意见）：
1. 弹道「打击目标」类型必须与 k043（箭对防空双倍伤害）一致：沿射线逐栋放大核对，
   线上无确认类型防空/高价值防御；无防空则照实写"双倍伤害未兑现"，低置信建筑标"类型待复核"、不编号。
2. 格坐标由负晶格任意原点换算为平台内 0–44 (col,row)（墙环四角单应，原点=上顶点T），
   图上加坐标轴小图；负坐标清零。
3. 三段走位每段写清"拆什么、为什么"。
4. 图例分三类来源：卡中数据(k037/k043) / 实测机制(compare.md §3) / 本图目视读点(待复核)。

底图: out/overlay/v6_l0_three_shot_base.png（905x1068）
平台单应: config/view_quads.json L0_snapped quad T/R/B/L -> (0,0)/(44,0)/(44,44)/(0,44)
数值: 仅取 knowledge/tactics/k037.json、k043.json 原文；卡中未给项显式标注。
不联网；不改任何现有 .py / info.json / config。
输出: out/overlay/v9_queen_giantarrow.png, out/overlay/v9_base_clean.png
"""
import os, math
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BASE = os.path.join(ROOT, "out", "overlay", "v6_l0_three_shot_base.png")
OUT_PLAN = os.path.join(ROOT, "out", "overlay", "v9_queen_giantarrow.png")
OUT_CLEAN = os.path.join(ROOT, "out", "overlay", "v9_base_clean.png")
FONT = r"C:\Windows\Fonts\msyh.ttc"
assert os.path.exists(FONT), "中文字体缺失"

# ---------- 平台内坐标单应：墙环四角 -> 44x44（原点=上顶点T） ----------
TQ = np.array([472., 118.]); RQ = np.array([878., 430.])
BQ = np.array([472., 758.]); LQ = np.array([68., 430.])
src = np.float32([TQ, RQ, BQ, LQ])
dst = np.float32([(0, 0), (44, 0), (44, 44), (0, 44)])
H_P = cv2.getPerspectiveTransform(src, dst)      # 图像 -> 平台
H_PINV = cv2.getPerspectiveTransform(dst, src)  # 平台 -> 图像

def plat_of(pxy):
    v = np.array([pxy[0], pxy[1], 1.0])
    w = H_P @ v
    return w[:2] / w[2]

def img_of(cr):
    v = np.array([cr[0], cr[1], 1.0])
    w = H_PINV @ v
    return w[:2] / w[2]

def cr_str(pt):
    c, r = plat_of(pt)
    return f"({c:.1f},{r:.1f})"

# ---------- 放大（2x，倍数未变，base_clean 同步） ----------
SCALE = 2.0
base = Image.open(BASE).convert("RGB")
W0, H0 = base.size
big = base.resize((int(W0 * SCALE), int(H0 * SCALE)), Image.LANCZOS)
W, H = big.size
SX = SY = SCALE

def S(pt):
    return (pt[0] * SX, pt[1] * SY)

# ---------- 计划点（1x 底图像素；平台格位由脚本现算） ----------
S_LAND = (150, 460)   # 女王落点（西缘外）
A_EDGE = (215, 445)   # ①清边止点
B_CORNER = (265, 455) # ②切角点
C_CORE = (385, 470)   # ③进中点
Q_SKILL = (235, 458)  # 开技能点（箭线起点，落在②段线上）
RAY_END = (795, 443)  # 箭线终点（东缘，目视读点）

# 线上建筑序列（沿 Q→RAY_END 由近及远，逐栋放大核对；均不编号为打击目标）
SEQ = [
    (1, "大型彩色机械（疑展示/攻城机器）·类型待复核", (258, 472), "穿其顶部 ±15px", "待复核"),
    (2, "深色尖塔·疑巨石碑monolith·类型待复核", (388, 468), "穿塔身上部 ±10px", "待复核"),
    (3, "部落城堡CC（金黑横幅确认，非防御地标）", (500, 468), "穿横幅上沿 ±8px", "高（地标）"),
    (4, "大本营（橙金穹顶，目视相对置信）", (700, 450), "穿穹顶 ±12px", "相对置信"),
]
# 线外备注（路线/主军另拆，目视读点待复核；非箭线目标）
OFFLINE = [
    ("地狱塔（南，熔岩环+火焰顶，目视相对置信）", (455, 640)),
    ("法师塔（西，白紫塔，目视）", (300, 385)),
    ("法师塔（北，白紫塔，目视）", (455, 175)),
]

# ---------- 画板 ----------
BAND = 780
canvas = Image.new("RGB", (W, H + BAND), (248, 246, 240))
canvas.paste(big, (0, 0))
dr = ImageDraw.Draw(canvas, "RGBA")

# 淡平台参考网格（每4格浅绿点线，便于对着数；仅内环可见）
def plat_grid_faint(step=4):
    for c in range(0, 45, step):
        p0 = S(img_of((c, 0))); p1 = S(img_of((c, 44)))
        dr.line([p0, p1], fill=(120, 190, 120, 35), width=1)
    for r in range(0, 45, step):
        p0 = S(img_of((0, r))); p1 = S(img_of((44, r)))
        dr.line([p0, p1], fill=(120, 190, 120, 35), width=1)
plat_grid_faint(4)

# ---------- 箭头工具 ----------
def arrowhead(p_tip, p_from, color, size=16):
    v = np.array(p_tip) - np.array(p_from)
    v = v / (np.linalg.norm(v) + 1e-9)
    n = np.array([-v[1], v[0]])
    tip = np.array(p_tip)
    a = tip - size * v + 0.55 * size * n
    b = tip - size * v - 0.55 * size * n
    dr.polygon([tuple(tip), tuple(a), tuple(b)], fill=color)

def seg(p0, p1, color, width=6, dashed=False, head=True):
    p0s, p1s = S(p0), S(p1)
    if dashed:
        n = 26
        for k in range(0, n, 2):
            t0, t1 = k / n, (k + 1) / n
            pa = tuple(np.array(p0s) * (1 - t0) + np.array(p1s) * t0)
            pb = tuple(np.array(p0s) * (1 - t1) + np.array(p1s) * t1)
            dr.line([pa, pb], fill=color, width=width)
    else:
        dr.line([p0s, p1s], fill=color, width=width)
    if head:
        arrowhead(p1s, p0s, color, size=18)

# ---------- 三段走位 ----------
C_CYAN = (0, 190, 220, 255)
C_ORANGE = (255, 140, 30, 255)
C_GREEN = (40, 175, 80, 255)
seg(S_LAND, A_EDGE, C_CYAN, width=7)
seg(A_EDGE, B_CORNER, C_ORANGE, width=7, dashed=True)
seg(B_CORNER, C_CORE, C_GREEN, width=7)

# ---------- 穿云箭弹道 ----------
C_ARROW = (220, 40, 40, 255)
dr.line([S(Q_SKILL), S(RAY_END)], fill=C_ARROW, width=9)
arrowhead(S(RAY_END), S(Q_SKILL), C_ARROW, size=20)

# ---------- 线上建筑：中性灰圈，不编号（无确认类型打击目标） ----------
for _, name, pt, _, conf in SEQ:
    x, y = S(pt)
    col = (150, 150, 150, 220) if conf == "待复核" else (90, 90, 90, 220)
    dr.ellipse([x - 30, y - 30, x + 30, y + 30], outline=col, width=4)

# ---------- 线外备注：蓝虚圈 ----------
for _, pt in OFFLINE:
    x, y = S(pt)
    box = [x - 32, y - 32, x + 32, y + 32]
    for k in range(0, 360, 2):
        a0 = math.radians(k); a1 = math.radians(k + 14)
        dr.arc(box, math.degrees(a0), math.degrees(a1), fill=(60, 120, 230, 255), width=4)

# ---------- 文字 ----------
F_TITLE = ImageFont.truetype(FONT, 40)
F_BIG = ImageFont.truetype(FONT, 26)
F_MID = ImageFont.truetype(FONT, 22)
F_SM = ImageFont.truetype(FONT, 19)
F_XS = ImageFont.truetype(FONT, 16)

def label_box(xy, s, font=F_SM, fill=(20, 20, 20, 255), bg=(255, 255, 255, 215)):
    x, y = xy
    b = dr.textbbox((x, y), s, font=font)
    dr.rectangle([b[0] - 6, b[1] - 4, b[2] + 6, b[3] + 4], fill=bg)
    dr.text((x, y), s, font=font, fill=fill)

# 走位点标注（平台格位）
label_box(S((70, 400)), f"女王落点 {cr_str(S_LAND)}｜k043:落地先处理贴边外点(edge_dist≤5)")
label_box(S((150, 480)), f"①清边止 {cr_str(A_EDGE)}")
label_box(S((272, 408)), f"②切角 {cr_str(B_CORNER)}")
label_box(S((330, 486)), f"③进中 {cr_str(C_CORE)}")
label_box(S((300, 436)), f"开技能点 {cr_str(Q_SKILL)}（箭线起点）", bg=(255, 235, 235, 220))

# 线上建筑短标签（序列全名见底部表）
label_box(S((198, 552)), f"线上① {cr_str(SEQ[0][2])}·类型待复核", font=F_XS, bg=(245, 245, 245, 220))
label_box(S((345, 566)), f"线上② {cr_str(SEQ[1][2])}·类型待复核", font=F_XS, bg=(245, 245, 245, 220))
label_box(S((452, 528)), f"线上③ 部落城堡 {cr_str(SEQ[2][2])}", font=F_XS, bg=(245, 245, 245, 220))
label_box(S((628, 366)), f"线上④ 大本营 {cr_str(SEQ[3][2])}", font=F_XS, bg=(245, 245, 245, 220))

for name, pt, lab in [
    (OFFLINE[0][0], OFFLINE[0][1], (392, 678)),
    (OFFLINE[1][0], OFFLINE[1][1], (232, 342)),
    (OFFLINE[2][0], OFFLINE[2][1], (400, 140)),
]:
    label_box(S(lab), f"线外另拆｜{name} {cr_str(pt)}", font=F_XS, bg=(225, 235, 255, 220))

# 弹道标注
label_box(S((600, 428)), "穿云箭弹道 k043：女王→目标连线｜射程/穿透上限:卡中未给",
          font=F_XS, bg=(255, 235, 235, 225))

# ---------- 坐标轴小图（左上）：原点=T上顶点，col向右，row向下 ----------
ax0 = S((18, 18))
ax_w, ax_h = 380, 176
dr.rectangle([ax0[0], ax0[1], ax0[0] + ax_w, ax0[1] + ax_h], fill=(255, 255, 255, 230), outline=(90, 90, 90, 255), width=2)
ox, oy = ax0[0] + 46, ax0[1] + 42
dr.ellipse([ox - 5, oy - 5, ox + 5, oy + 5], fill=(0, 0, 0, 255))
dr.text((ox - 10, oy - 26), "0=(0,0) 原点·墙环上顶点T", font=F_XS, fill=(0, 0, 0, 255))
dr.line([ox, oy, ox + 120, oy], fill=(0, 0, 200, 255), width=3)
arrowhead((ox + 120, oy), (ox, oy), (0, 0, 200, 255), size=12)
dr.text((ox + 124, oy - 14), "col →", font=F_MID, fill=(0, 0, 200, 255))
dr.line([ox, oy, ox, oy + 80], fill=(0, 130, 0, 255), width=3)
arrowhead((ox, oy + 80), (ox, oy), (0, 130, 0, 255), size=12)
dr.text((ox + 8, oy + 84), "row ↓", font=F_MID, fill=(0, 130, 0, 255))
dr.text((ax0[0] + 12, ax0[1] + ax_h - 24), "平台内坐标 (col,row) 0–44｜原点=墙环上顶点",
       font=F_XS, fill=(60, 60, 60, 255))

# ---------- 防空未兑现 红色警示条（两行，居中不出血） ----------
warn1 = "⚠ 本条弹道不覆盖防空：全图目视未见防空火箭，k043「对防空双倍伤害」未兑现"
warn2 = "（本线不满足一箭串2–3座防空；需另选同射线串防空的站位再开技能）"
w1 = dr.textbbox((0, 0), warn1, font=F_BIG)
w2 = dr.textbbox((0, 0), warn2, font=F_SM)
bw = max(w1[2] - w1[0], w2[2] - w2[0])
wx, wy = S((250, 318))
dr.rectangle([wx - 12, wy - 10, wx + bw + 24, wy + 78], fill=(255, 235, 235, 235), outline=(200, 30, 30, 255), width=3)
dr.text((wx, wy), warn1, font=F_BIG, fill=(190, 20, 20, 255))
dr.text((wx, wy + 40), warn2, font=F_SM, fill=(150, 30, 30, 255))

# ---------- 底部数据带 ----------
band_y = H
dr.rectangle([0, band_y, W, H + BAND], fill=(245, 243, 236, 255))
dr.line([0, band_y, W, band_y], fill=(120, 110, 90, 255), width=2)

y = band_y + 14
dr.text((24, y), "TH16 女王穿云箭战术图（k037 根骑士+女巫 / k043 Giant Arrow）｜底图 v6_l0_three_shot_base.png｜坐标=平台内(col,row)0–44",
        font=F_BIG, fill=(30, 30, 30, 255))

col_x = [24, 620, 1180]
blocks = [
    (col_x[0], "【图例】来源分类见下三组", [
        "青实线①清边 / 橙虚线②切角 / 绿实线③进中（女王三段走位）",
        "红粗线 穿云箭弹道（k043:箭线=女王→目标连线）",
        "灰圈 线上建筑（序列见下表；未编号=非确认打击目标）",
        "蓝虚圈 线外另拆（主军/副部队处理，非箭线目标）",
        "平台网格每4格一条；坐标 (col,row) 0–44，原点=墙环上顶点",
    ]),
    (col_x[1], "【卡中数据 k037/k043 原文】", [
        "k037: 根骑士6–8、女巫5–6、冰戈仑1–2、治疗天使2–3、",
        "弓手4–5断边；法术 狂暴2–3/治疗1/冰冻1–2/地震3–4；",
        "女王 Giant Arrow，永王地面 Eternal Tome；先3–4地震砸核心",
        "隔间，两侧断边每侧≥2–3栋，女王箭点优先鹰炮/monolith。",
        "k043: 箭线=女王与目标中心点连线；对防空双倍伤害；",
        "狂暴不加成箭伤；箭可穿全阵、可击空中部队与英雄；",
        "落地先处理贴边防空(edge_dist≤5)，箭线从外往内扫；",
        "一箭串线防空后再放主军。",
    ]),
    (col_x[2], "【实测机制 compare.md §3（他阵实例，仅证机制）】", [
        "03阵 箭线(1,27)→(29,16) 串 AD(15,21)/(18,21)/(21,19) 三座；",
        "05阵 箭线(9,38)→(1,10) 串 AD(0,19)/(0,16)/(4,26) 三座。",
        "（注：实例坐标为他阵自身格系，非本图平台坐标）",
        "",
        "【本图目视读点（待复核，需实阵逐栋确认）】",
        "线上①②类型、线外塔型、大本营/城堡辨识均为截图放大",
        "目视，低置信处已标“待复核”；本图未见到蓝色防空碟。",
    ]),
]
for cx, title, items in blocks:
    yy = y + 44
    dr.text((cx, yy), title, font=F_MID, fill=(150, 60, 0, 255))
    yy += 30
    for it in items:
        dr.text((cx, yy), "· " + it, font=F_SM, fill=(40, 40, 40, 255))
        yy += 26

# 线上建筑序列表（全宽）
ty = band_y + 340
dr.text((24, ty), "【线上建筑序列】沿箭线由近及远（平台格位；无确认类型防空，故无编号打击目标）", font=F_MID, fill=(150, 60, 0, 255))
ty += 32
hdr = "序号 | 类型（目视） | 平台格位(col,row) | 是否在线上(±px) | 类型置信"
dr.text((30, ty), hdr, font=F_SM, fill=(0, 0, 0, 255))
ty += 26
for no, name, pt, off, conf in SEQ:
    dr.text((30, ty), f"{no} | {name} | {cr_str(pt)} | {off} | {conf}", font=F_SM, fill=(40, 40, 40, 255))
    ty += 26

ty += 8
dr.text((24, ty), "【防空核对结论】全图目视未见防空火箭（蓝碟）→ 本条弹道不覆盖防空，对防空双倍伤害未兑现；",
        font=F_MID, fill=(190, 20, 20, 255))
ty += 28
dr.text((24, ty), "若本阵防空存在，需另选一条同射线串2–3座防空的站位再开技能（k043选线逻辑），本图走位仅作女王推进参考。",
        font=F_SM, fill=(120, 30, 30, 255))
ty += 30

# 三段目的
dr.text((24, ty), "【三段走位目的】", font=F_MID, fill=(150, 60, 0, 255))
ty += 28
for line in [
    "①清边 落点(6.6,41.5)→(9.1,37.0)：拆西外缘角部建筑（目视：西缘储物/角楼，类型待复核），把左边界拉成直线，逼主军向内、不追外飘（k037断边每侧≥2–3栋）。",
    "②切角 (9.1,37.0)→(12.5,35.0)：拐进西角隔间打开缺口、清掉角部零散建筑（类型待复核），为女王切出进中通道；开技能点(11.1,36.8)在本段线上。",
    "③进中 (12.5,35.0)→(20.0,29.5)：女王贴身沿内墙推进核心外缘，抵达进中点；本段不承诺箭伤，箭线仅作穿云射线标注。",
]:
    dr.text((30, ty), "· " + line, font=F_SM, fill=(40, 40, 40, 255))
    ty += 26

ty += 6
dr.text((24, ty), "【卡中未给（不臆造）】女王等级/技能等级；巨箭射程(格)；穿透硬上限(栋)；箭伤数值口径。",
        font=F_SM, fill=(150, 30, 30, 255))
ty += 28
# 比例尺：2x 放大（1x 底图像素）
px_per_tile = 24.0 * SCALE
bar = int(px_per_tile)
dr.line([24, ty + 16, 24 + bar, ty + 16], fill=(0, 0, 0, 255), width=4)
dr.line([24, ty + 10, 24, ty + 22], fill=(0, 0, 0, 255), width=3)
dr.line([24 + bar, ty + 10, 24 + bar, ty + 22], fill=(0, 0, 0, 255), width=3)
dr.text((24, ty + 28), "比例尺: 本图2x放大，1格≈48px（1x底图 1格≈24px，链测23.8–24.4）；平台坐标为墙环单应，不等同晶格格。",
        font=F_SM, fill=(40, 40, 40, 255))

canvas.save(OUT_PLAN)
# 干净底图（仅放大，无标注；2x 倍数未变，同步覆盖）
base_big = base.resize((int(W0 * SCALE), int(H0 * SCALE)), Image.LANCZOS)
base_big.save(OUT_CLEAN)
print("saved", OUT_PLAN, canvas.size)
print("saved", OUT_CLEAN, base_big.size)
for nm, pt in [("落点", S_LAND), ("A", A_EDGE), ("B", B_CORNER), ("C", C_CORE), ("Q", Q_SKILL), ("END", RAY_END)]:
    print(nm, pt, "plat", cr_str(pt))
for no, name, pt, off, conf in SEQ:
    print("SEQ", no, cr_str(pt), conf)
