# -*- coding: utf-8 -*-
"""
b14_queen_giantarrow.py — 14号敌阵 kekejdj 女王走位 + 穿云箭复核图（纯离线程序化叠加，新文件）

底图: out/overlay/enemy/b14_full.png（ov1 1280x720 裁口 195,88-1065,582 -> 870x494）
quad: config/view_quads.json enemy_preview_14 T(640,58) R(1105,325) B(640,600) L(167,308)
      -> 平台内 (col,row) 0-44（原点=T，col沿T→R，row沿T→L），双线性单应
尺度: 宽边 L→R=938px/44 ≈ 21.3px/格（投影各向异性，无单一正交标量）
数值: 仅 k037/k043 原文；卡中未给项显式标注。
说明: 本预览低分辨率，目视确认防空 0 座；2 座侧翼红蓝顶塔为低置信候选(类型待复核)，
      不硬画串线，候选给单独射线。不改现有 .py/info.json/config；纯离线。
输出: out/overlay/v9b_queen_giantarrow_b14.png, out/overlay/v9b_b14_clean.png
"""
import os, math
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EN = os.path.join(ROOT, "out", "overlay", "enemy")
OUT_PLAN = os.path.join(ROOT, "out", "overlay", "v9b_queen_giantarrow_b14.png")
OUT_CLEAN = os.path.join(ROOT, "out", "overlay", "v9b_b14_clean.png")
FONT = r"C:\Windows\Fonts\msyh.ttc"
assert os.path.exists(FONT), "中文字体缺失"

# ---------- quad 单应（ov1 1280x720 帧坐标） ----------
TQ = np.array([640., 58.]); RQ = np.array([1105., 325.])
BQ = np.array([640., 600.]); LQ = np.array([167., 308.])
src = np.float32([TQ, RQ, BQ, LQ])
dst = np.float32([(0, 0), (44, 0), (44, 44), (0, 44)])
H_P = cv2.getPerspectiveTransform(src, dst)
H_PINV = cv2.getPerspectiveTransform(dst, src)
CROP = (195, 88, 1065, 582)  # ov1 -> b14_full

def plat_of(ov):
    v = np.array([ov[0], ov[1], 1.0]); w = H_P @ v
    return w[:2] / w[2]

def img_of(cr):
    v = np.array([cr[0], cr[1], 1.0]); w = H_PINV @ v
    return w[:2] / w[2]

def cr_str(ov):
    c, r = plat_of(ov)
    return f"({c:.1f},{r:.1f})"

# ---------- 底图（ov1 裁口 = b14_full 同源，直接用 ov1 再裁，保证单应一致） ----------
buf = np.fromfile(os.path.join(EN, "b14_ov1.png"), dtype=np.uint8)
ov1 = cv2.imdecode(buf, cv2.IMREAD_COLOR)
x1, y1, x2, y2 = CROP
base = ov1[y1:y2, x1:x2]
SCALE = 2.0
base_pil = Image.fromarray(cv2.cvtColor(base, cv2.COLOR_BGR2RGB))
W0, H0 = base_pil.size
big = base_pil.resize((int(W0 * SCALE), int(H0 * SCALE)), Image.LANCZOS)
W, H = big.size

def S(ov):
    """ov1 帧 -> 画布（裁口偏移 + 放大）"""
    return ((ov[0] - CROP[0]) * SCALE, (ov[1] - CROP[1]) * SCALE)

# ---------- 计划点（ov1 像素，平台格位由脚本现算） ----------
S_LAND = (330, 235)   # 女王落点（西北外草地，贴边）
A_EDGE = (385, 295)   # ①清边止
B_CORNER = (435, 335) # ②切角（西北角隔间）
C_CORE = (525, 365)   # ③进中（核心外缘）
Q_SKILL = (400, 315)  # 开技能点（②段线上，待复核选点）

# 候选防空（低置信，类型待复核；不编号为确认目标）
CAND_AD = [
    ("候选AD-L 侧翼红蓝顶塔（类型待复核）", (315, 350), (288, 312)),
    ("候选AD-R 侧翼红蓝顶塔（类型待复核）", (962, 350), (990, 312)),
]
# 目视可辨地标（待复核）
LANDMARKS = [
    ("大本营 TH（橙金穹顶，目视相对置信）", (640, 330)),
    ("巨石碑 monolith（暗金方尖碑，待复核）", (430, 375)),
    ("部落城堡 CC（紫冠屋，目视）", (560, 540)),
    ("透明法术塔（隐形，待复核）", (646, 156)),
]

# ---------- 画板 ----------
BAND = 780
canvas = Image.new("RGB", (W, H + BAND), (248, 246, 240))
canvas.paste(big, (0, 0))
dr = ImageDraw.Draw(canvas, "RGBA")

# 淡平台网格（每4格）
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

# ---------- 候选AD 单独射线（灰虚线，待复核，不串线） ----------
C_RAY = (150, 150, 150, 255)
for name, ad, stand in CAND_AD:
    seg(stand, ad, C_RAY, width=4, dashed=True, head=True)

# ---------- 标记 ----------
def circle(ov, color, r=32, width=4, dashed=False):
    x, y = S(ov)
    box = [x - r, y - r, x + r, y + r]
    if dashed:
        for k in range(0, 360, 2):
            a0 = math.radians(k); a1 = math.radians(k + 14)
            dr.arc(box, math.degrees(a0), math.degrees(a1), fill=color, width=width)
    else:
        dr.ellipse(box, outline=color, width=width)

for _, ad, _ in CAND_AD:
    circle(ad, (190, 120, 0, 255), r=30, width=4, dashed=True)
for name, pt in LANDMARKS:
    circle(pt, (110, 110, 110, 200), r=28, width=3)

# ---------- 文字 ----------
F_TITLE = ImageFont.truetype(FONT, 38)
F_BIG = ImageFont.truetype(FONT, 25)
F_MID = ImageFont.truetype(FONT, 21)
F_SM = ImageFont.truetype(FONT, 18)
F_XS = ImageFont.truetype(FONT, 15)

def label_box(xy, s, font=F_SM, fill=(20, 20, 20, 255), bg=(255, 255, 255, 215)):
    x, y = xy
    b = dr.textbbox((x, y), s, font=font)
    dr.rectangle([b[0] - 6, b[1] - 4, b[2] + 6, b[3] + 4], fill=bg)
    dr.text((x, y), s, font=font, fill=fill)

# 走位点
label_box(S((238, 288)), f"女王落点 {cr_str(S_LAND)}｜k043:落地先处理贴边外点(edge_dist≤5)")
label_box(S((360, 268)), f"①清边止 {cr_str(A_EDGE)}")
label_box(S((418, 308)), f"②切角 {cr_str(B_CORNER)}")
label_box(S((500, 340)), f"③进中 {cr_str(C_CORE)}")
dr.ellipse([S(Q_SKILL)[0] - 8, S(Q_SKILL)[1] - 8, S(Q_SKILL)[0] + 8, S(Q_SKILL)[1] + 8],
           fill=(255, 235, 235, 230), outline=(200, 30, 30, 255), width=2)
label_box(S((350, 348)), f"开技能点 {cr_str(Q_SKILL)}（待复核）", font=F_XS, bg=(255, 235, 235, 220))

# 地标
label_box(S((590, 300)), f"大本营 {cr_str(LANDMARKS[0][1])}", font=F_XS)
label_box(S((385, 405)), f"巨石碑 {cr_str(LANDMARKS[1][1])}·待复核", font=F_XS)
label_box(S((520, 566)), f"CC {cr_str(LANDMARKS[2][1])}", font=F_XS)
label_box(S((560, 272)), f"透明法术塔 {cr_str(LANDMARKS[3][1])}·待复核", font=F_XS)

# 候选AD 射线标注
label_box(S((235, 300)), f"候选AD-L {cr_str(CAND_AD[0][1])}·待复核｜单独射线 女王站{cr_str(CAND_AD[0][2])}",
          font=F_XS, bg=(250, 245, 230, 225))
label_box(S((790, 255)), f"候选AD-R {cr_str(CAND_AD[1][1])}·待复核｜单独射线 女王站{cr_str(CAND_AD[1][2])}",
          font=F_XS, bg=(250, 245, 230, 225))

# ---------- 坐标轴小图（左上） ----------
ax0 = S((205, 96))
ax_w, ax_h = 252, 138
dr.rectangle([ax0[0], ax0[1], ax0[0] + ax_w, ax0[1] + ax_h], fill=(255, 255, 255, 230), outline=(90, 90, 90, 255), width=2)
ox, oy = ax0[0] + 40, ax0[1] + 36
dr.ellipse([ox - 5, oy - 5, ox + 5, oy + 5], fill=(0, 0, 0, 255))
dr.text((ox - 10, oy - 26), "0=(0,0) 原点·墙环上顶点T", font=F_XS, fill=(0, 0, 0, 255))
dr.line([ox, oy, ox + 120, oy], fill=(0, 0, 200, 255), width=3)
arrowhead((ox + 120, oy), (ox, oy), (0, 0, 200, 255), size=12)
dr.text((ox + 124, oy - 14), "col →", font=F_MID, fill=(0, 0, 200, 255))
dr.line([ox, oy, ox, oy + 80], fill=(0, 130, 0, 255), width=3)
arrowhead((ox, oy + 80), (ox, oy), (0, 130, 0, 255), size=12)
dr.text((ox + 8, oy + 84), "row ↓", font=F_MID, fill=(0, 130, 0, 255))
dr.text((ax0[0] + 12, ax0[1] + ax_h - 22), "平台内坐标 (col,row) 0–44｜quad 双线性单应", font=F_XS, fill=(60, 60, 60, 255))

# ---------- 防空未确认 红色警示 ----------
warn1 = "⚠ 本预览目视确认防空 0 座：未见蓝色防空碟；仅2座侧翼红蓝顶塔为低置信候选(类型待复核)"
warn2 = "无法选一串2–3座的共线射线；候选AD给单独射线，需实阵侦察复核后再定开技能线"
wx, wy = S((370, 200))
w1 = dr.textbbox((0, 0), warn1, font=F_BIG); w2 = dr.textbbox((0, 0), warn2, font=F_SM)
bw = max(w1[2] - w1[0], w2[2] - w2[0])
dr.rectangle([wx - 12, wy - 10, wx + bw + 24, wy + 72], fill=(255, 235, 235, 235), outline=(200, 30, 30, 255), width=3)
dr.text((wx, wy), warn1, font=F_BIG, fill=(190, 20, 20, 255))
dr.text((wx, wy + 38), warn2, font=F_SM, fill=(150, 30, 30, 255))

# ---------- 底部数据带 ----------
band_y = H
dr.rectangle([0, band_y, W, H + BAND], fill=(245, 243, 236, 255))
dr.line([0, band_y, W, band_y], fill=(120, 110, 90, 255), width=2)
y = band_y + 14
dr.text((24, y), "14号 kekejdj 女王穿云箭战术图（k037 根骑士+女巫 / k043 Giant Arrow）｜底图 b14_full.png｜坐标=平台内(col,row)0–44",
        font=F_BIG, fill=(30, 30, 30, 255))

col_x = [24, 600, 1160]
blocks = [
    (col_x[0], "【图例】来源分类见下三组", [
        "青实线①清边 / 橙虚线②切角 / 绿实线③进中（女王三段走位）",
        "灰虚线=候选AD单独射线（待复核）｜灰圈=目视地标",
        "平台网格每4格一条；坐标(col,row)0–44，原点=墙环上顶点T",
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
        "03阵 箭线(1,27)→(29,16) 串 AD(15,21)/(18,21)/(21,19)；",
        "05阵 箭线(9,38)→(1,10) 串 AD(0,19)/(0,16)/(4,26)。",
        "（实例坐标为他阵自身格系，非本图平台坐标）",
        "",
        "【本图目视读点（待复核，需实阵逐栋确认）】",
        "防空/建筑类型均为预览放大目视；分辨率低、部分被墙遮挡，",
        "低置信处已标“待复核”；本图未见蓝色防空碟。",
    ]),
]
for cx, title, items in blocks:
    yy = y + 42
    dr.text((cx, yy), title, font=F_MID, fill=(150, 60, 0, 255))
    yy += 28
    for it in items:
        dr.text((cx, yy), "· " + it, font=F_SM, fill=(40, 40, 40, 255))
        yy += 25

ty = band_y + 330
dr.text((24, ty), "【防空定位与射线】目视确认 0 座；低置信候选2座（侧翼红蓝顶塔，类型待复核）；",
        font=F_MID, fill=(190, 20, 20, 255))
ty += 28
dr.text((24, ty), "该图找不到4座防空：预览分辨率低/建筑被墙与邻舍遮挡，可能漏判，需实阵侦察复核。无确认共线防空→不硬画串线；",
        font=F_SM, fill=(120, 30, 30, 255))
ty += 26
dr.text((24, ty), "候选AD-L " + cr_str(CAND_AD[0][1]) + " 单独射线: 女王站" + cr_str(CAND_AD[0][2]) + "→射向候选塔；候选AD-R " + cr_str(CAND_AD[1][1]) + " 单独射线: 女王站" + cr_str(CAND_AD[1][2]) + "→射向候选塔；",
        font=F_SM, fill=(40, 40, 40, 255))
ty += 26
dr.text((24, ty), "两候选不共线、类型未确认，无法一串多；实阵确认防空后按 k043 另选同射线站位。",
        font=F_SM, fill=(40, 40, 40, 255))
ty += 32

dr.text((24, ty), "【三段走位目的】", font=F_MID, fill=(150, 60, 0, 255))
ty += 28
for line in [
    "①清边 落点" + cr_str(S_LAND) + "→" + cr_str(A_EDGE) + "：拆西北外缘角部建筑（金仓/雕像/角楼，类型待复核），把西北边界拉直，逼主军向内不追外飘；配弓手4–5（k037断边每侧≥2–3栋）。",
    "②切角 " + cr_str(A_EDGE) + "→" + cr_str(B_CORNER) + "：拐进西北角隔间打开缺口、清掉角部零散建筑，为女王切出进中通道；开技能点" + cr_str(Q_SKILL) + "在本段线上（待复核）。",
    "③进中 " + cr_str(B_CORNER) + "→" + cr_str(C_CORE) + "：女王贴内墙推进核心外缘；主军冰戈仑1–2顶首轮，根骑士6–8 spread一线，女巫5–6跟进，治疗天使2–3吊前排；",
    "　　配合3–4地震先砸核心隔间墙，进核心落狂暴，多头地狱塔露头即冰冻（k037原文）。",
]:
    dr.text((30, ty), "· " + line, font=F_SM, fill=(40, 40, 40, 255))
    ty += 26

ty += 6
dr.text((24, ty), "【卡中未给（不臆造）】女王等级/技能等级；巨箭射程(格)；穿透硬上限(栋)；箭伤数值口径；敌方英雄等级/CC援军/陷阱位置。",
        font=F_SM, fill=(150, 30, 30, 255))
ty += 28
# 比例尺：宽边 L→R 938px/44 ≈21.3px/格（ov1帧，2x放大后≈42.6px/格）
px_per_tile = 938.0 / 44 * SCALE
bar = int(px_per_tile)
dr.line([24, ty + 16, 24 + bar, ty + 16], fill=(0, 0, 0, 255), width=4)
dr.line([24, ty + 10, 24, ty + 22], fill=(0, 0, 0, 255), width=3)
dr.line([24 + bar, ty + 10, 24 + bar, ty + 22], fill=(0, 0, 0, 255), width=3)
dr.text((24, ty + 28), f"比例尺: 2x放大；宽边938px/44，1格≈{938/44:.1f}px(ov1帧)/≈{px_per_tile:.0f}px(本图)；quad投影各向异性，格边长随方向略变。",
        font=F_SM, fill=(40, 40, 40, 255))

canvas.save(OUT_PLAN)
clean = Image.fromarray(cv2.cvtColor(base, cv2.COLOR_BGR2RGB))
clean = clean.resize((W0, H0), Image.LANCZOS)
clean.save(OUT_CLEAN)
print("saved", OUT_PLAN, canvas.size)
print("saved", OUT_CLEAN, clean.size)
for nm, pt in [("落点", S_LAND), ("A", A_EDGE), ("B", B_CORNER), ("C", C_CORE), ("Q", Q_SKILL)]:
    print(nm, pt, "plat", cr_str(pt))
for nm, ad, stand in CAND_AD:
    print("CAND", nm, "ad", cr_str(ad), "stand", cr_str(stand))
for nm, pt in LANDMARKS:
    print("LM", nm, cr_str(pt))
