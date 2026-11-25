# -*- coding: utf-8 -*-
"""HUD 绘制：marks.json 的 marks/lines/pins/circles（steps 策略正文不上 HUD）。

坐标口径（P0）：tile -> 渲染像素只走 geo.Calib 单应矩阵；渲染 1280x720
再按窗口客户区缩放。禁止使用 hud.py 线性插值。
配色沿用 hud.py：YELLOW #f0c452 / ORANGE #e27a38 / GREEN #60c882 /
BLUE #78bee6 / INK #eef0f2 / GREY #969ca0。
"""
from __future__ import annotations
import math
import time

from . import theme

# 配色（A 方案，RGBA 0..1；HUD 层不带蓝紫相）
YELLOW = theme.WARN
ORANGE = (0.886, 0.478, 0.220, 1.0)
GREEN = theme.SUCCESS
BLUE = theme.RANK_R1  # 旧蓝圆 -> 低档石板灰，不再是亮蓝
INK = theme.INK
GREY = theme.SUB
# 重要防御三档（rank 实色，与 pages 同一 token；只作描边/圆/序号，不铺面板底）
HOT = theme.RANK_R3
MID = theme.RANK_R2
LOW_COL = theme.RANK_R1

# 面板开合时间戳（pages.draw_panel 每帧刷新；draw_important 据 0.5s 新鲜度判定面板是否打开，
# 无需改 runtime 调用签名）。面板打开时，落进面板矩形的标注整体跳过（C9）。
_panel_seen_t = 0.0


def mark_panel_open() -> None:
    """由 pages.draw_panel 每帧调用：记录面板最近绘制时间。"""
    global _panel_seen_t
    _panel_seen_t = time.time()


def _panel_rect(win_w: float):
    """按 A 方案面板宽公式自算面板矩形（无 runtime 入参）。返回 (x0, x1)。"""
    pw = theme.panel_width(win_w)
    return win_w - pw, win_w


def _inside_panel(x: float, y: float, win_w: float, win_h: float) -> bool:
    """面板 0.5s 内刚画过（=PANEL 态）且点落在面板矩形内 -> True。"""
    if time.time() - _panel_seen_t > 0.5:
        return False
    x0, x1 = _panel_rect(win_w)
    return x0 <= x <= x1 and 0.0 <= y <= win_h


def _text_outline(dl, x, y, text, col) -> None:
    """白字 1px 黑描边（C9）：四向暗边垫底，主色字在上。不改字位。"""
    stroke = theme.HUD_STROKE
    for dx, dy in ((-1.0, 0.0), (1.0, 0.0), (0.0, -1.0), (0.0, 1.0)):
        dl.add_text(imgui_pt(x + dx, y + dy), _col(stroke), text)
    dl.add_text(imgui_pt(x, y), _col(col), text)


# 标签碰撞避让（开关，默认关；theme.HUD_LABEL_AVOID=1 才启用；C9）。
# 默认关闭时坐标原样返回，绝不挪动（主线 draw_important 验证不得作废）。
_AVOID_CELL = 16.0


def _avoid_spot(x, y, win_w, win_h, occupied):
    if not theme.HUD_LABEL_AVOID:
        return x, y
    for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1),
                   (-1, -1), (1, -1), (-1, 1), (1, 1)):
        nx, ny = x + dx * _AVOID_CELL, y + dy * _AVOID_CELL
        if nx < 0 or ny < 0 or nx > win_w - 60 or ny > win_h - 16:
            continue
        if all(abs(nx - ox) >= 14 or abs(ny - oy) >= 14 for ox, oy in occupied):
            occupied.append((nx, ny))
            return nx, ny
    return x, y


def _col(rgba):
    from imgui_bundle import imgui
    return imgui.color_convert_float4_to_u32(imgui.ImVec4(*rgba))


def _tp(calib, gx, gy, sx, sy):
    x, y = calib.tile_to_px(float(gx), float(gy))
    return x * sx, y * sy


def draw_marks(dl, calib, marks: dict, win_w: float, win_h: float) -> None:
    """在前景绘制层上画全部标注。dl 为 ImGui 前景 draw list。"""
    sx, sy = win_w / 1280.0, win_h / 720.0

    # ---- marks[]：目标/规避建筑 ----
    for m in marks.get("marks") or []:
        tile = m.get("tile")
        if not (isinstance(tile, (list, tuple)) and len(tile) == 2 and calib is not None):
            continue
        x, y = _tp(calib, tile[0], tile[1], sx, sy)
        if _inside_panel(x, y, win_w, win_h):
            continue  # C9：面板打开时不把标注画进面板矩形
        role = m.get("role")
        seq = m.get("seq")
        if role == "target":
            dl.add_circle(imgui_pt(x, y), 10.0, _col(ORANGE), 0, 2.0)
            if seq is not None:
                _text_outline(dl, x + 13, y - 7, str(seq), INK)
        else:  # avoid / 其它
            dl.add_circle(imgui_pt(x, y), 6.0, _col(BLUE), 0, 1.5)
        label = m.get("label")
        if label:
            _text_outline(dl, x + 10, y + 8, str(label), GREY)

    # ---- lines[]：容忍 {from,to} 或 points 列表 ----
    for ln in marks.get("lines") or []:
        if not isinstance(ln, dict):
            continue
        a = ln.get("from") or ln.get("a")
        b = ln.get("to") or ln.get("b")
        if a and b and calib is not None:
            ax, ay = _tp(calib, a[0], a[1], sx, sy)
            bx, by = _tp(calib, b[0], b[1], sx, sy)
            dl.add_line(imgui_pt(ax, ay), imgui_pt(bx, by), _col(YELLOW), 2.0)

    # ---- pins[]：英雄/部队入场点 ----
    for p in marks.get("pins") or []:
        tile = p.get("tile")
        if not (isinstance(tile, (list, tuple)) and len(tile) == 2 and calib is not None):
            continue
        x, y = _tp(calib, tile[0], tile[1], sx, sy)
        if _inside_panel(x, y, win_w, win_h):
            continue
        # 菱形标记（箭头）；pin 的 label/note/count 是策略入点文案，不上 HUD（任务2）
        d = 8.0
        dl.add_line(imgui_pt(x, y - d), imgui_pt(x + d, y), _col(YELLOW), 2.0)
        dl.add_line(imgui_pt(x + d, y), imgui_pt(x, y + d), _col(YELLOW), 2.0)
        dl.add_line(imgui_pt(x, y + d), imgui_pt(x - d, y), _col(YELLOW), 2.0)
        dl.add_line(imgui_pt(x - d, y), imgui_pt(x, y - d), _col(YELLOW), 2.0)

    # ---- circles[]：法术/冰冻半径（tile 半径 -> 屏幕半径近似） ----
    for c in marks.get("circles") or []:
        tile = c.get("tile")
        r = c.get("radius", 3)
        if not (isinstance(tile, (list, tuple)) and len(tile) == 2 and calib is not None):
            continue
        x, y = _tp(calib, tile[0], tile[1], sx, sy)
        if _inside_panel(x, y, win_w, win_h):
            continue
        # 一格边长屏幕近似 = (sx+sy)/2 * 32（44 格跨菱形半宽）
        pr = float(r) * (sx + sy) / 2.0 * 18.0
        dl.add_circle(imgui_pt(x, y), pr, _col(GREEN), 48, 1.5)

    # ---- steps[]：策略正文不上 HUD（任务2/G4）----
    # marks.json.steps 是策略步骤文本，属于面板策略内容；HUD 只画箭头/圆点/标签/
    # 圆圈，不再把 steps[:2] 渲染到左下角，避免策略正文盖住游戏画面。


def imgui_pt(x, y):
    from imgui_bundle import imgui
    return imgui.ImVec2(float(x), float(y))


# ---------------------------------------------------------------- 引擎模式：重要防御标注

def draw_important(dl, calib, rows, sel_idx, win_w, win_h) -> None:
    """本地模式标注：按威胁档配色画出重要防御，聚焦项加粗放大并带名字/dps。

    rows 由 overlay.tactics.load_local 提供（tile 坐标）；坐标换算只走 calib.tile_to_px，
    与 marks 标注同一口径，避免两套标定混用。win 为渲染客户区，按 1280x720 缩放。
    """
    if calib is None or not rows:
        return
    sx, sy = win_w / 1280.0, win_h / 720.0
    # 一格的屏幕步长（渲染坐标系）
    ax, ay = calib.tile_to_px(0.0, 0.0)
    bx, by = calib.tile_to_px(1.0, 0.0)
    cx, cy = calib.tile_to_px(0.0, 1.0)
    tile_x = abs(bx - ax) or 22.0
    tile_y = abs(cy - ay) or 11.0

    occupied: list = []
    for i, r in enumerate(rows):
        tile = r.get("tile")
        if not (isinstance(tile, (list, tuple)) and len(tile) == 2):
            continue
        x, y = _tp(calib, tile[0], tile[1], sx, sy)
        if _inside_panel(x, y, win_w, win_h):
            continue  # C9：面板打开时不把标注画进面板矩形
        rank = int(r.get("rank", 1))
        col = HOT if rank >= 3 else (MID if rank == 2 else LOW_COL)
        sel = (i == int(sel_idx))
        if sel:
            hw = 1.6 * tile_x * sx
            hh = 1.1 * tile_y * sy
            dl.add_rect_filled(imgui_pt(x - hw, y - hh), imgui_pt(x + hw, y + hh),
                               col=_col((col[0], col[1], col[2], 0.20)), rounding=3.0)
            dl.add_rect(imgui_pt(x - hw, y - hh), imgui_pt(x + hw, y + hh),
                        col=_col(col), rounding=3.0, thickness=2.5)
            label = f"{r.get('name', '')}"
            if r.get("dps"):
                label += f" {r['dps']}"
            # 标签位置原样（x-hw, y-hh-15）；避让开关默认关，不改坐标
            lx, ly = _avoid_spot(x - hw, y - hh - 15.0, win_w, win_h, occupied)
            _text_outline(dl, lx, ly, label, INK)
        else:
            dl.add_circle(imgui_pt(x, y), 8.0, _col((col[0], col[1], col[2], 0.80)), 0, 1.8)
            dl.add_text(imgui_pt(x + 10.0, y - 6.0),
                        _col((col[0], col[1], col[2], 0.90)), str(i + 1))


# ---------------------------------------------------------------- v5：LLM 策略标注
#
# 独立新函数 draw_plan_marks；不动 draw_marks / draw_important 的既有坐标逻辑。
# threats：编号圆环（rank1 红 #E5484D / rank2 橙 #E8A33D），右侧 ≤4 字短标签 +
#   1px 深色描边 + alpha 0.72 深色小底（亮草/雪地/夜间可读，H5）；
# route：青 #3AA6C9 数字圆点，相邻序号虚线箭头，起点标「进」；
# 截断：威胁 ≤5、路线 ≤6，超额直接省略（不淡化，H3）；解析失败 marks 为空 -> 0 标注。

PLAN_T1 = (0.898, 0.282, 0.302, 1.0)      # #E5484D rank1 红
PLAN_T2 = (0.910, 0.639, 0.239, 1.0)      # #E8A33D rank2 橙
PLAN_ROUTE = (0.227, 0.651, 0.788, 1.0)   # #3AA6C9 青
PLAN_LABEL_BG = (0.05, 0.06, 0.08, 0.72)  # 标签小底 alpha≈0.72


def _dash_arrow(dl, ax, ay, bx, by, col):
    """a->b 虚线 + 末端小箭头；手动分段（imgui 无原生虚线）。"""
    dx, dy = bx - ax, by - ay
    dist = math.hypot(dx, dy) or 1.0
    ux, uy = dx / dist, dy / dist
    dash, gap, t = 8.0, 5.0, 0.0
    while t < dist:
        t2 = min(t + dash, dist)
        dl.add_line(imgui_pt(ax + ux * t, ay + uy * t),
                    imgui_pt(ax + ux * t2, ay + uy * t2), _col(col), 1.8)
        t = t2 + gap
    ang = math.atan2(dy, dx)
    s = 7.0
    dl.add_line(imgui_pt(bx, by),
                imgui_pt(bx - s * math.cos(ang - 0.5), by - s * math.sin(ang - 0.5)),
                _col(col), 1.8)
    dl.add_line(imgui_pt(bx, by),
                imgui_pt(bx - s * math.cos(ang + 0.5), by - s * math.sin(ang + 0.5)),
                _col(col), 1.8)


def draw_plan_marks(dl, calib, marks: dict, win_w: float, win_h: float,
                    show_threats: bool = True, show_route: bool = True) -> None:
    """LLM 模式策略标注：威胁环 + 路线青点虚线。marks 为空/None 直接返回（R1）。"""
    if calib is None or not marks:
        return
    sx, sy = win_w / 1280.0, win_h / 720.0
    threats = (marks.get("threats") or [])[:5]   # H3：超额省略，不淡化
    route = (marks.get("route") or [])[:6]

    # ---- 路线：先虚线箭头连点，再画青点压住线端 ----
    if show_route:
        pts = []
        for r in route:
            tile = r.get("tile")
            if not (isinstance(tile, (list, tuple)) and len(tile) == 2):
                continue
            x, y = _tp(calib, tile[0], tile[1], sx, sy)
            if _inside_panel(x, y, win_w, win_h):
                continue
            pts.append((x, y, r))
        for (ax, ay, _a), (bx, by, _b) in zip(pts, pts[1:]):
            _dash_arrow(dl, ax, ay, bx, by, PLAN_ROUTE)
        for i, (x, y, r) in enumerate(pts):
            dl.add_circle(imgui_pt(x, y), 7.0, _col(PLAN_ROUTE), 0, 1.8)
            tag = "进" if i == 0 else str(r.get("seq", i + 1))
            dl.add_text(imgui_pt(x - 4.0, y - 6.0), _col(INK), tag)

    # ---- 威胁：编号圆环 + 右侧 ≤4 字短标签（0.72 小底 + 1px 描边） ----
    if show_threats:
        for i, t in enumerate(threats):
            tile = t.get("tile")
            if not (isinstance(tile, (list, tuple)) and len(tile) == 2):
                continue
            x, y = _tp(calib, tile[0], tile[1], sx, sy)
            if _inside_panel(x, y, win_w, win_h):
                continue
            rank = int(t.get("rank", 1))
            col = PLAN_T1 if rank == 1 else PLAN_T2
            dl.add_circle(imgui_pt(x, y), 9.0, _col(col), 0, 2.0)
            dl.add_text(imgui_pt(x - 3.0, y - 6.0), _col(INK), str(i + 1))
            label = str(t.get("label") or "")[:4]
            if label:
                from imgui_bundle import imgui as _imgui
                tx, ty = x + 14.0, y - 7.0
                tw = _imgui.calc_text_size(label).x
                dl.add_rect_filled(imgui_pt(tx - 4.0, ty - 3.0),
                                   imgui_pt(tx + tw + 4.0, ty + 15.0),
                                   col=_col(PLAN_LABEL_BG), rounding=3.0)
                _text_outline(dl, tx, ty, label, INK)


def draw_plan_phases(dl, calib, plan: dict, win_w: float, win_h: float,
                     t_now=None, show_threats: bool = True,
                     show_route: bool = True) -> None:
    """schema v2 phases 图层（HUD 1280x720 实尺）。

    plan_render.imgui_phase_layer 的半径/字号按 2400px 离线图标定，落到 1280x720
    HUD 会缩没（圆标~20px、数字 6px 级）；此处不改 plan_render，只取其
    PHASE_COLORS / phase_at_t，几何按 HUD 实尺重算：
      序号圆标 r=17（直径 34）、数字居中、阶段短标签在圆标右上方；
      路线段线宽 3；投放点 r=10；目标圈 r=16/线宽 3；威胁红圈 r=18/线宽 3。
    t_now=None 时不高亮（现网无战斗时钟，不伪造）；逐点 _inside_panel 剔除面板内点。
    """
    if calib is None or not plan:
        return
    from .plan_render import PHASE_COLORS, phase_at_t
    from imgui_bundle import imgui
    sx, sy = win_w / 1280.0, win_h / 720.0

    def proj(tile):  # tile -> 1280x720 虚拟坐标（复刻 draw_plan_marks 的 _tp）
        x, y = _tp(calib, tile[0], tile[1], sx, sy)
        return (x, y)

    # SEL 开关裁切：show_route 关 -> 不画阶段；show_threats 关 -> 不画威胁
    phases = (plan.get("phases") or []) if show_route else []
    threats = (plan.get("threats") or []) if show_threats else []
    if not phases and not threats:
        return

    active = phase_at_t(plan, t_now) if t_now is not None else None

    def _dim(rgb, alpha):
        return (rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0, alpha)

    def _short(ph, i):
        name = str(ph.get("name") or "")
        return (name[2:4] if len(name) >= 4 else name[:4]) or str(ph.get("i", i + 1))

    # ---- 圆标锚点最小间距松弛：相邻 tile 投影挨太近时沿连线推开，
    # 保证圆标（r17）与短标签 0 相交；只挪标记位，不动路线/目标投影 ----
    anchors = []
    for ph in phases:
        r0 = (ph.get("route") or [None])[0]
        anchors.append(proj(r0) if r0 is not None else None)
    MIN_D = 46.0
    for _ in range(16):
        for i in range(len(anchors)):
            for j in range(i + 1, len(anchors)):
                if anchors[i] is None or anchors[j] is None:
                    continue
                ax, ay = anchors[i]
                bx, by = anchors[j]
                dx, dy = bx - ax, by - ay
                d = math.hypot(dx, dy) or 1.0
                if d < MIN_D:
                    push = (MIN_D - d) / 2.0
                    ux, uy = dx / d, dy / d
                    anchors[i] = (ax - ux * push, ay - uy * push)
                    anchors[j] = (bx + ux * push, by + uy * push)

    # 短标签候选方位：右上前/右下/左上前/左下/正左/正右，逐个试，挑第一个
    # 不压邻圆标与已放标签的方位（贪心避让，保证 0 相交）
    label_cands = [(26.0, -28.0), (26.0, 14.0), (-26.0, -28.0),
                   (-26.0, 14.0), (-30.0, -8.0), (30.0, -8.0)]

    def _hit(box, others, pad=2.0):
        x0, y0, x1, y1 = box
        for ox0, oy0, ox1, oy1 in others:
            if min(x1, ox1) - max(x0, ox0) > pad and \
               min(y1, oy1) - max(y0, oy0) > pad:
                return True
        return False

    placed_labels = []

    # ---- phases：路线段 + 序号圆标(实色) + 短标签 + 投放点 + 目标圈 ----
    for i, ph in enumerate(phases):
        rgb = PHASE_COLORS[i % len(PHASE_COLORS)]
        dim = 0.35 if active is not None and active != i else 1.0
        col_line = _dim(rgb, dim)
        col_opaque = _dim(rgb, 1.0)
        raw_route = ph.get("route") or []
        route = [proj(p) for p in raw_route]
        for a, b in zip(route, route[1:]):
            if _inside_panel(a[0], a[1], win_w, win_h) or \
               _inside_panel(b[0], b[1], win_w, win_h):
                continue
            dl.add_line(imgui_pt(a[0], a[1]), imgui_pt(b[0], b[1]),
                        _col(col_line), 3.0)
        if route and anchors[i] is not None:
            bx, by = anchors[i]
            if not _inside_panel(bx, by, win_w, win_h):
                dl.add_circle_filled(imgui_pt(bx, by), 17.0, _col(col_opaque))
                num = str(ph.get("i", i + 1))
                tw = imgui.calc_text_size(num).x
                dl.add_text(imgui_pt(bx - tw / 2.0, by - 8.0),
                            _col((0.10, 0.11, 0.14, 1.0)), num)
                lab = _short(ph, i)
                lw = imgui.calc_text_size(lab).x
                # 邻圆标 bbox（排除自身）+ 已放标签，挑第一个不相交方位
                others = []
                for k, ac in enumerate(anchors):
                    if k == i or ac is None:
                        continue
                    ox0, oy0 = ac
                    others.append((ox0 - 19.0, oy0 - 19.0, ox0 + 19.0, oy0 + 19.0))
                others.extend(placed_labels)
                lx, ly = bx + 26.0, by - 28.0
                for ox, oy in label_cands:
                    cx = bx + ox
                    if ox < 0:  # 左侧方位按文字宽回退
                        cx = bx + ox - lw
                    if cx < 8.0 or cx + lw > win_w - 8.0:
                        continue
                    box = (cx, by + oy, cx + lw, by + oy + 18.0)
                    if not _hit(box, others):
                        lx, ly = cx, by + oy
                        break
                placed_labels.append((lx, ly, lx + lw, ly + 18.0))
                dl.add_text(imgui_pt(lx, ly), _col(col_opaque), lab)
        for u in ph.get("units") or []:
            dt = u.get("drop_tile")
            if not dt:
                continue
            # 投放点与 route[0] 重合（入口圆标已标）则不重复画，避免压标
            if raw_route and list(dt) == list(raw_route[0]):
                continue
            dx, dy = proj(dt)
            if _inside_panel(dx, dy, win_w, win_h):
                continue
            dl.add_circle_filled(imgui_pt(dx, dy), 10.0, _col(col_line))
            cnt = int(u.get("count") or 1)
            if cnt > 1:
                dl.add_text(imgui_pt(dx + 14.0, dy - 9.0),
                            _col(_dim(rgb, dim)), f"x{cnt}")
        for tg in ph.get("targets") or []:
            tx, ty = proj(tg)
            if _inside_panel(tx, ty, win_w, win_h):
                continue
            dl.add_circle(imgui_pt(tx, ty), 16.0, _col(col_line), 32, 3.0)

    # ---- threats：红圈 r=18/线宽 3 + 左右短刻线 ----
    for th in threats:
        tile = th.get("tile")
        if not tile:
            continue
        tx, ty = proj(tile)
        if _inside_panel(tx, ty, win_w, win_h):
            continue
        red = (229, 72, 77)
        dl.add_circle(imgui_pt(tx, ty), 18.0, _col(_dim(red, 1.0)), 32, 3.0)
        dl.add_line(imgui_pt(tx - 9.0, ty), imgui_pt(tx - 3.0, ty),
                    _col(_dim(red, 1.0)), 2.0)
        dl.add_line(imgui_pt(tx + 3.0, ty), imgui_pt(tx + 9.0, ty),
                    _col(_dim(red, 1.0)), 2.0)
