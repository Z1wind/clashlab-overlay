# -*- coding: utf-8 -*-
"""P3c-1 女王穿云箭战术图：真实阵图底图 + 撒兵环 + 穿云箭直线箭头 + 被穿防御高亮编号 + 阶段色条。

已有能力边界（先读代码确认，不重复实现）：
  - plan_render.render_plan 把 plan.phases 当「通用虚线路线 + 瞄准圈」渲染，**没有**穿云箭直线
    与穿刺目标高亮；giant-arrow 在 plan 里只是一个 unit 类型（投放点菱形 + 数量）。
  - clashlab/plan_marks.py:108 giant_arrow() 是规则选线器（sim/ring -> from/to/hits），产出
    draw_calls，由 ui.py 在 HUD 上画；不产出独立战术图 PNG。
本模块补齐的独立交付：render_giant_arrow_diagram(layout, plan, out_png, title=...)。

数据来源：
  - layout: bases/th16/**/layout.json（dict 或路径）；用于撒兵环与建筑足迹。
  - plan:   schema v2 plan.json（phases[].units 里 type=="giant-arrow"）。
  - 撒兵环复用 analysis.deployment_ring（真算法，不另写一套）。
  - 被穿判定 = 建筑中心到 from->to 直线的垂直距离 ≤ tol 格且投影在 [0,1] 内，
    与 plan_marks.giant_arrow 的 ARROW_HIT_TOL 同口径（默认 1.2 格）。

CLI（仓库根目录）：
  & 'D:\\Python313\\python.exe' -m clashlab.overlay.giant_arrow_diagram \
      --layout bases/th16/03/layout.json --plan out/overlay/_plan_viz/plan_03_llm.json \
      --base bases/th16/03/base.png --quad "1288,12;2314,569;1281,1193;282,562" \
      --out out/overlay/_p3c/giant_arrow_03.png --title "03 阵 · 女王穿云箭"
"""
from __future__ import annotations

import argparse
import json
import math
import os

from PIL import Image, ImageDraw

from . import plan_render as _pr


# ---------------------------------------------------------------- 纯函数（可单测）

def _xy(t):
    return [float(t[0]), float(t[1])]


def giant_arrow_spec(plan):
    """schema v2 plan -> 第一个含 giant-arrow 单位的阶段摘要；没有返回 None。

    from = 单位 drop_tile（缺省退回 route[0]）；to = route[-1]（缺省退回最后一个 target）。
    """
    try:
        phases = (plan or {}).get("phases") or []
    except AttributeError:
        return None
    for i, ph in enumerate(phases):
        units = [u for u in (ph.get("units") or [])
                 if isinstance(u, dict) and u.get("type") == "giant-arrow"]
        if not units:
            continue
        route = [_xy(p) for p in (ph.get("route") or [])
                 if isinstance(p, (list, tuple)) and len(p) >= 2]
        targets = [_xy(p) for p in (ph.get("targets") or [])
                   if isinstance(p, (list, tuple)) and len(p) >= 2]
        frm = None
        for u in units:
            dt = u.get("drop_tile")
            if isinstance(dt, (list, tuple)) and len(dt) >= 2:
                frm = _xy(dt)
                break
        if frm is None and route:
            frm = list(route[0])
        to = list(route[-1]) if route else (list(targets[-1]) if targets else None)
        if frm is None or to is None:
            continue
        return {
            "phase_index": i,
            "index": ph.get("i", i + 1),
            "name": ph.get("name") or "",
            "t_start": _f(ph.get("t_start"), 0.0),
            "t_end": _f(ph.get("t_end"), 0.0),
            "from": frm,
            "to": to,
            "route": route,
            "targets": targets,
            "units": units,
            "purpose": ph.get("purpose") or "",
        }
    return None


def _f(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


AIR_DEFENSE = "air-defense"      # 防空火箭（放空）
AIR_SWEEPER = "air-sweeper"        # 吹风机
AIR_TARGETS = {AIR_DEFENSE, AIR_SWEEPER}
HIDDEN_TYPES = {"hidden-tesla"}    # 默认不现形，不能当已确认目标


def summarize_hits(hits):
    """被穿目标分类：防空火箭 / 吹风机 / 特斯拉(隐身) / 其它。"""
    ad = sum(1 for h in hits if h.get("type") == AIR_DEFENSE)
    sw = sum(1 for h in hits if h.get("type") == AIR_SWEEPER)
    tesla = sum(1 for h in hits if h.get("type") in HIDDEN_TYPES)
    return {"total": len(hits), "air_defense": ad, "air_sweeper": sw,
            "air_total": ad + sw, "tesla_hidden": tesla,
            "other": len(hits) - ad - sw - tesla}


def match_skewered(layout, frm, to, tol=1.2):
    """被穿建筑：中心到 from->to 直线垂直距离 <= tol 格，且投影 t ∈ [-0.02, 1.02]。

    返回按 t 升序（沿箭线方向）排列的 [{type, tile, t, perp, order}]，order 从 1 编号。
    只吃 layout["buildings"]；墙不算防御目标。
    """
    try:
        buildings = (layout or {}).get("buildings") or []
    except AttributeError:
        return []
    try:
        fx, fy = float(frm[0]), float(frm[1])
        tx, ty = float(to[0]), float(to[1])
    except (TypeError, ValueError, IndexError):
        return []
    dx, dy = tx - fx, ty - fy
    l2 = dx * dx + dy * dy
    if l2 <= 1e-9:
        return []
    length = math.sqrt(l2)
    hits = []
    for b in buildings:
        tile = b.get("tile") if isinstance(b, dict) else None
        try:
            x, y = float(tile[0]), float(tile[1])
        except (TypeError, ValueError, IndexError):
            continue
        wx, wy = x - fx, y - fy
        t = (wx * dx + wy * dy) / l2
        if t < -0.02 or t > 1.02:
            continue
        perp = abs(wx * dy - wy * dx) / length
        if perp > float(tol):
            continue
        typ = b.get("type") or ""
        hits.append({"type": typ, "tile": [int(round(x)), int(round(y))],
                     "t": round(t, 4), "perp": round(perp, 3),
                     "air": typ in AIR_TARGETS, "hidden": typ in HIDDEN_TYPES})
    hits.sort(key=lambda h: h["t"])
    for i, h in enumerate(hits):
        h["order"] = i + 1
    return hits


# ---------------------------------------------------------------- 工具

def _load_layout(layout):
    """layout 可为 dict 或 json 路径；返回 (dict, 路径或 None)。"""
    if isinstance(layout, dict):
        return layout, None
    if isinstance(layout, str):
        with open(layout, "r", encoding="utf-8") as f:
            return json.load(f), layout
    return {}, None


def _size_of(typ):
    """建筑尺寸（格）：与 plan_render.load_footprints 同口径。"""
    size = _pr._DEFAULT_FOOTPRINT_SIZE.get(typ)
    if size is None:
        try:
            from ..assets import stats
            size = stats(typ, th=16).get("size")
        except Exception:
            size = None
    try:
        return float(size or 3)
    except (TypeError, ValueError):
        return 3.0


def _footprint_poly(proj, tile, size):
    half = float(size) / 2.0
    tx, ty = float(tile[0]), float(tile[1])
    return [proj((tx - half, ty - half)), proj((tx + half, ty - half)),
            proj((tx + half, ty + half)), proj((tx - half, ty + half))]


def _deploy_ring(layout):
    """真撒兵环（复用 analysis.deployment_ring）；异常返回 None。"""
    try:
        from . import sim_panel
        from .. import analysis
        sim = sim_panel._sim_from_layout(layout)
        return analysis.deployment_ring(sim, margin=1)
    except Exception:
        return None


def _ring_cells(ring):
    try:
        ys, xs = ring.nonzero()
        return list(zip(xs.tolist(), ys.tolist()))
    except Exception:
        return []


def _parse_quad(s):
    if not s:
        return None
    pts = []
    for chunk in str(s).split(";"):
        xy = chunk.strip().split(",")
        if len(xy) == 2:
            pts.append([float(xy[0]), float(xy[1])])
    return pts if len(pts) == 4 else None


# ---------------------------------------------------------------- 主渲染

def render_giant_arrow_diagram(layout, plan, out_png, title="女王穿云箭战术图",
                               base=None, quad=None, tol=1.2, dim_base=0.72):
    """出穿云箭战术图 PNG；返回 PIL Image（同时写 out_png）。"""
    layout, layout_path = _load_layout(layout)
    if base is None and layout_path:
        cand = os.path.join(os.path.dirname(os.path.abspath(layout_path)), "base.png")
        base = cand if os.path.exists(cand) else None

    # ---- 画布/底图
    if base and os.path.exists(base):
        im = Image.open(base).convert("RGB")
        if dim_base < 1.0:
            dark = Image.new("RGB", im.size, _pr.BG)
            im = Image.blend(dark, im, dim_base)
    else:
        im = Image.new("RGB", (1280, 1000), _pr.BG)
    W, H = im.size
    d = ImageDraw.Draw(im, "RGBA")
    if base and os.path.exists(base):
        if quad is None:  # 没有 quad 时按整图近似（仅兜底，正式出图必须给 quad）
            quad = [[0, 0], [W, 0], [W, H], [0, H]]
        proj = _pr.Projector(quad, canvas_wh=(W, H))
    else:
        proj = _pr.Projector(None, canvas_wh=(W, H))
        m = proj.margin
        for g in range(0, 45, 5):
            gx = m + g / 44 * (W - 2 * m)
            gy = m + g / 44 * (H - 2 * m)
            d.line([gx, m, gx, H - m], fill=_pr.GRID, width=1)
            d.line([m, gy, W - m, gy], fill=_pr.GRID, width=1)

    fs_title = max(24, W // 52)
    fs = max(16, W // 78)
    fs_sm = max(13, W // 110)
    f_title = _pr._font(fs_title, True)
    f_lab = _pr._font(fs)
    f_sm = _pr._font(fs_sm)
    f_badge = _pr._font(fs, True)

    spec = giant_arrow_spec(plan)
    phases = (plan or {}).get("phases") or []
    hits = []
    if spec:
        hits = match_skewered(layout, spec["from"], spec["to"], tol=tol)

    # ---- 1) 撒兵环：青绿半透明格点
    ring = _deploy_ring(layout)
    ring_cells = _ring_cells(ring)
    for (cx, cy) in ring_cells:
        poly = [proj((cx - 0.5, cy - 0.5)), proj((cx + 0.5, cy - 0.5)),
                proj((cx + 0.5, cy + 0.5)), proj((cx - 0.5, cy + 0.5))]
        d.polygon(poly, fill=_pr.TEAL + (96,), outline=_pr.TEAL + (165,))

    # ---- 2) 阶段色条（底部）：所有阶段按时长比例上色，穿云箭阶段白框高亮
    bar_h = max(26, int(H * 0.028))
    bar_y = H - bar_h - max(52, 2 * fs_sm + 20)
    pad_x = max(30, W // 34)
    if phases:
        ts = [_f(p.get("t_start")) for p in phases]
        te = [_f(p.get("t_end")) for p in phases]
        t_lo, t_hi = min(ts), max(te) or (max(ts) + 1.0)
        span = max(t_hi - t_lo, 1.0)
        d.rounded_rectangle([pad_x, bar_y, W - pad_x, bar_y + bar_h], radius=5,
                            fill=(16, 19, 24, 225), outline=_pr.SUB, width=2)
        for i, ph in enumerate(phases):
            a, b = _f(ph.get("t_start")), _f(ph.get("t_end"))
            x0 = pad_x + (a - t_lo) / span * (W - 2 * pad_x)
            x1 = pad_x + (b - t_lo) / span * (W - 2 * pad_x)
            col = _pr._phase_color(i)
            is_arrow = bool(spec and i == spec["phase_index"])
            d.rectangle([x0, bar_y, max(x1, x0 + 5), bar_y + bar_h],
                        fill=col + (235 if is_arrow else 165,),
                        outline=_pr.WHITE if is_arrow else None, width=3)
            seg_w = x1 - x0
            if seg_w >= 40:
                label = f"{ph.get('i', i + 1)}.{ph.get('name', '')} {a:.0f}-{b:.0f}s"
                tw = d.textlength(label, font=f_sm)
                if tw <= seg_w - 10:
                    d.text((x0 + (seg_w - tw) / 2, bar_y - fs_sm - 8), label,
                           font=f_sm, fill=_pr.INK if is_arrow else _pr.SUB)
                else:  # 窄段只放序号（段内可辨），全名走下方清单
                    num = str(ph.get("i", i + 1))
                    nw = d.textlength(num, font=f_badge)
                    d.text((x0 + (seg_w - nw) / 2, bar_y - fs_sm - 8), num,
                           font=f_badge, fill=_pr.INK if is_arrow else _pr.SUB)
        d.text((pad_x, bar_y + bar_h + 4),
               "阶段色条（◆=穿云箭阶段）", font=f_sm, fill=_pr.SUB)
        d.text((W - pad_x - 210, bar_y + bar_h + 4),
               f"{t_lo:.0f}s → {t_hi:.0f}s", font=f_sm, fill=_pr.SUB)
        cap = "　".join(
            (("◆" if (spec and i == spec["phase_index"]) else "·")
             + f"{ph.get('i', i + 1)} {ph.get('name', '')} "
               f"{_f(ph.get('t_start')):.0f}-{_f(ph.get('t_end')):.0f}s")
            for i, ph in enumerate(phases))
        d.text((pad_x, bar_y + bar_h + 6 + fs_sm), cap, font=f_sm, fill=_pr.SUB)

    # ---- 3) 穿云箭直线箭头：from -> to（暗描边 + 琥珀主线 + 大箭头）
    if spec:
        a = proj(spec["from"])
        b = proj(spec["to"])
        # 规划路线（若有折点）用淡虚线示意，主线仍是穿云箭直线
        pts = [proj(p) for p in spec["route"]]
        for p, q in zip(pts, pts[1:]):
            _pr._dash_arrow(d, p, q, _pr.AMBER + (120,), width=max(2, W // 400),
                            dash=18, gap=12, head=1)
        ux, uy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(ux, uy) or 1.0
        ux, uy = ux / ln, uy / ln
        head_len = max(26, int(W * 0.018))
        d.line([a, b], fill=(16, 19, 24, 230), width=max(10, W // 210))
        d.line([a, b], fill=_pr.AMBER, width=max(5, W // 330))
        # 箭头三角
        tip = (b[0] + ux * head_len * 0.6, b[1] + uy * head_len * 0.6)
        left = (b[0] - uy * head_len * 0.45, b[1] + ux * head_len * 0.45)
        right = (b[0] + uy * head_len * 0.45, b[1] - ux * head_len * 0.45)
        d.polygon([tip, left, right], fill=_pr.AMBER, outline=_pr.BG)
        # 起点标记（女王站位 / 撒兵点）
        d.ellipse([a[0] - 11, a[1] - 11, a[0] + 11, a[1] + 11],
                  fill=_pr.AMBER, outline=_pr.BG, width=2)
        _pr._label_pill(d, a[0] - 6, a[1] + 20,
                        f"起点 格({spec['from'][0]:.0f},{spec['from'][1]:.0f})", f_sm)
        dist_tiles = math.hypot(spec["to"][0] - spec["from"][0],
                                spec["to"][1] - spec["from"][1])
        mx = a[0] + 0.45 * (b[0] - a[0])
        my = a[1] + 0.45 * (b[1] - a[1])
        _pr._label_pill(d, mx - 200, my - fs - 34,
                        f"穿云箭直线 {dist_tiles:.1f} 格 · 被穿 {len(hits)} 座", f_sm)

    # ---- 4) 被穿防御高亮 + 编号
    for h in hits:
        if h["type"] == AIR_DEFENSE:
            col = _pr.THREAT_RED
        elif h["type"] == AIR_SWEEPER:
            col = _pr.AMBER
        elif h["type"] in HIDDEN_TYPES:
            col = (150, 150, 150)
        else:
            col = _pr.TEAL
        poly = _footprint_poly(proj, h["tile"], _size_of(h["type"]))
        d.polygon(poly, fill=col + (110,), outline=col + (255,))
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        bx, by = max(xs) + 8, min(ys) - 8
        r = max(14, int(fs * 1.05))
        d.ellipse([bx - r, by - r, bx + r, by + r], fill=col,
                  outline=_pr.INK, width=2)
        num = "?" if h["type"] in HIDDEN_TYPES else str(h["order"])
        tw = d.textlength(num, font=f_badge)
        d.text((bx - tw / 2, by - fs / 2 - 2), num, font=f_badge, fill=_pr.BG)

    # ---- 5) 标题条 + 概况 + 图例
    head_h = fs_title + 26
    d.rectangle([0, 0, W, head_h], fill=(22, 26, 32, 230))
    goal = (plan or {}).get("goal") or ""
    model = (plan or {}).get("model") or ""
    d.text((18, 10), f"{title}　目标：{goal}　{model}", font=f_title, fill=_pr.INK)
    if spec and spec.get("purpose"):
        d.text((22, head_h + 8), f"箭清目的：{spec['purpose']}", font=f_lab,
               fill=_pr.SUB)

    _hs = summarize_hits(hits)
    info = (f"撒兵环 {len(ring_cells)} 格 · 被穿 {_hs['total']} 座"
            f"（防空火箭×{_hs['air_defense']} · 吹风机×{_hs['air_sweeper']}"
            f" · 特斯拉隐身×{_hs['tesla_hidden']}）"
            + (f" · 箭线 {math.hypot(spec['to'][0]-spec['from'][0], spec['to'][1]-spec['from'][1]):.1f} 格"
               if spec else " · 无穿云箭阶段"))
    tw = d.textlength(info, font=f_lab)
    d.rounded_rectangle([W - tw - 44, head_h + 6, W - 16, head_h + fs + 16], radius=5,
                        fill=(16, 19, 24, 210), outline=_pr.SUB, width=1)
    d.text((W - tw - 30, head_h + 11), info, font=f_lab, fill=_pr.INK)

    lh = fs_sm + 9
    panel_w = max(470, int(W * 0.28))
    hits_part = (8 + lh + len(hits) * lh) if hits else 0
    panel_h = 34 + 4 * lh + hits_part + 8
    lx, ly = 26, max(26, bar_y - fs_sm - 24 - panel_h)
    d.rounded_rectangle([lx - 8, ly - 8, lx + panel_w, ly + panel_h], radius=6,
                        fill=(16, 19, 24, 215), outline=_pr.SUB, width=1)
    _warn = tesla_warning(layout)
    if _warn:
        d.text((lx, ly), _warn, font=f_sm, fill=_pr.AMBER)
        ly += lh
    d.text((lx, ly), "图例", font=f_lab, fill=_pr.INK)
    legend = [(_pr.TEAL, "撒兵环=可撒兵格（analysis.deployment_ring）"),
              (_pr.AMBER, "琥珀直线箭头=女王穿云箭 from→to"),
              (_pr.THREAT_RED, "红=防空火箭（放空）；橙=吹风机；灰?=特斯拉（默认不现形）"),
              (_pr.AMBER, "底部色条=阶段时序（白框=穿云箭阶段）")]
    for k, (col, txt) in enumerate(legend):
        y = ly + 34 + k * lh
        if k == 1:
            d.line([lx, y + 7, lx + 34, y + 7], fill=col, width=5)
        else:
            d.ellipse([lx + 2, y + 1, lx + 16, y + 15], outline=col, width=3)
        d.text((lx + 44, y), txt, font=f_sm, fill=_pr.SUB)
    if hits:
        y = ly + 34 + 4 * lh + 8
        d.text((lx, y), f"被穿防御（按箭线顺序，垂直距离 ≤ {tol:g} 格）",
               font=f_sm, fill=_pr.THREAT_RED)
        for h in hits:
            y += lh
            name = _pr._zh_of(h["type"]) or h["type"]
            if h["type"] == AIR_DEFENSE:
                mark = "◉"
            elif h["type"] == AIR_SWEEPER:
                mark = "◍"
            elif h["type"] in HIDDEN_TYPES:
                mark = "?"
            else:
                mark = "○"
            d.text((lx, y),
                   f"{h['order']} {mark} {name} 格({h['tile'][0]},{h['tile'][1]}) "
                   f"偏 {h['perp']:.2f} 格", font=f_sm, fill=_pr.SUB)

    if out_png:
        out_dir = os.path.dirname(os.path.abspath(out_png))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        im.save(out_png)
    return im


def diagram_facts(layout, plan, base=None, quad=None, tol=1.2):
    """出图关键坐标/数字（证据用）：画布尺寸、from/to 像素、被穿列表、环格数、箭线长度。"""
    layout, layout_path = _load_layout(layout)
    if base is None and layout_path:
        cand = os.path.join(os.path.dirname(os.path.abspath(layout_path)), "base.png")
        base = cand if os.path.exists(cand) else None
    if base and os.path.exists(base):
        with Image.open(base) as im:
            W, H = im.size
        q = quad if quad is not None else [[0, 0], [W, 0], [W, H], [0, H]]
        proj = _pr.Projector(q, canvas_wh=(W, H))
        mode = "quad"
    else:
        W, H = 1280, 1000
        proj = _pr.Projector(None, canvas_wh=(W, H))
        mode = "plain"
    spec = giant_arrow_spec(plan)
    hits = match_skewered(layout, spec["from"], spec["to"], tol=tol) if spec else []
    ring = _deploy_ring(layout)
    facts = {"canvas_wh": [W, H], "mode": mode,
             "ring_cells": len(_ring_cells(ring)),
             "tol": tol,
             "hits": hits}
    if spec:
        fpx = [round(float(v), 2) for v in proj(spec["from"])]
        tpx = [round(float(v), 2) for v in proj(spec["to"])]
        facts.update({
            "spec": {k: spec[k] for k in ("phase_index", "index", "name",
                                          "t_start", "t_end", "from", "to")},
            "from_px": fpx, "to_px": tpx,
            "arrow_len_tiles": round(math.hypot(spec["to"][0] - spec["from"][0],
                                                spec["to"][1] - spec["from"][1]), 2),
        })
    facts["hits_px"] = [{"order": h["order"], "type": h["type"], "tile": h["tile"],
                         "px": [round(float(v), 2) for v in proj(h["tile"])]}
                        for h in hits]
    return facts


# ---------------------------------------------------------------- CLI

def main(argv=None):
    ap = argparse.ArgumentParser(description="女王穿云箭战术图（离屏 PNG）")
    ap.add_argument("--layout", required=True, help="layout.json 路径（或含 base.png 的阵目录下）")
    ap.add_argument("--plan", required=True, help="schema v2 plan.json 路径")
    ap.add_argument("--out", required=True, help="输出 PNG 路径")
    ap.add_argument("--base", default="", help="底图 PNG（省略则用 layout 同目录 base.png）")
    ap.add_argument("--quad", default="", help="四角 x,y;x,y;x,y;x,y（上右下左）")
    ap.add_argument("--title", default="女王穿云箭战术图")
    ap.add_argument("--tol", type=float, default=1.2, help="被穿判定垂直容差（格）")
    args = ap.parse_args(argv)

    with open(args.plan, "r", encoding="utf-8") as f:
        plan = json.load(f)
    quad = _parse_quad(args.quad)
    base = args.base or None
    facts = diagram_facts(args.layout, plan, base=base, quad=quad, tol=args.tol)
    im = render_giant_arrow_diagram(args.layout, plan, args.out, title=args.title,
                                    base=base, quad=quad, tol=args.tol)
    print(json.dumps({"out": args.out, "size": list(im.size), "facts": facts},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# ---------------------------------------------------------------- 自动选线
# 评分口径：吹风机 3 分（影响整片空军路线）> 防空火箭 2 分 > 其它防御 1 分；
# 特斯拉默认不现形，不确定收益，按 -0.5 计（把它穿掉是运气，不是计划）。
_AIR_SCORE = {AIR_SWEEPER: 3.0, AIR_DEFENSE: 2.0}
_OTHER_DEF_SCORE = 1.0
_TESLA_PENALTY = -0.5


def _defense_types():
    try:
        from clashlab import assets
        return set(assets.STATS.keys())
    except Exception:
        return {AIR_DEFENSE, AIR_SWEEPER, "cannon", "archer-tower", "mortar", "wizard-tower",
                "x-bow", "inferno-tower", "scattershot", "eagle-artillery", "monolith",
                "bomb-tower", "hidden-tesla"}


def score_hits(hits):
    """给一组命中打分（越高越好）。"""
    defs = _defense_types()
    s = 0.0
    for h in hits:
        typ = h.get("type")
        if typ in _AIR_SCORE:
            s += _AIR_SCORE[typ]
        elif typ in HIDDEN_TYPES:
            s += _TESLA_PENALTY
        elif typ in defs:
            s += _OTHER_DEF_SCORE
    return round(s, 2)


def _clip_line(p, q, grid=44):
    """把过 p、q 的无限直线用 slab 法裁到 [0,grid]^2，返回端点或 None。"""
    import math as _m
    x1, y1 = float(p[0]), float(p[1])
    x2, y2 = float(q[0]), float(q[1])
    dx, dy = x2 - x1, y2 - y1
    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
        return None
    lo, hi = -1e9, 1e9
    for origin, delta in ((x1, dx), (y1, dy)):
        if abs(delta) < 1e-9:
            if origin < 0 or origin > grid:
                return None
            continue
        t0 = (0.0 - origin) / delta
        t1 = (float(grid) - origin) / delta
        if t0 > t1:
            t0, t1 = t1, t0
        lo = max(lo, t0)
        hi = min(hi, t1)
    if hi - lo < 1e-6:
        return None
    a = (x1 + dx * lo, y1 + dy * lo)
    b = (x1 + dx * hi, y1 + dy * hi)
    if _m.hypot(b[0] - a[0], b[1] - a[1]) < 6:
        return None
    return [round(a[0], 2), round(a[1], 2)], [round(b[0], 2), round(b[1], 2)]


def candidate_arrow_lines(layout, grid=44, tol=1.2):
    """候选箭线：每座对空目标过点的 4 个方向 + 两座对空目标的连线（裁到地图内）。"""
    import math as _m
    air = []
    for b in (layout or {}).get("buildings") or []:
        if isinstance(b, dict) and b.get("type") in AIR_TARGETS:
            try:
                air.append((float(b["tile"][0]), float(b["tile"][1])))
            except Exception:
                continue
    raw = []
    for (x, y) in air:
        for ang in (0, 45, 90, 135):
            rad = _m.radians(ang)
            dx, dy = _m.cos(rad), _m.sin(rad)
            raw.append(((x, y), (x + dx, y + dy)))
    for i in range(len(air)):
        for j in range(i + 1, len(air)):
            raw.append((air[i], air[j]))
    seen = set()
    out = []
    for p, q in raw:
        seg = _clip_line(p, q, grid)
        if not seg:
            continue
        a, b = seg
        key = (round(a[0], 1), round(a[1], 1), round(b[0], 1), round(b[1], 1))
        key2 = (round(b[0], 1), round(b[1], 1), round(a[0], 1), round(a[1], 1))
        if key in seen or key2 in seen:
            continue
        seen.add(key)
        hits = match_skewered(layout, a, b, tol=tol)
        out.append({"from": list(a), "to": list(b), "hits": hits,
                    "score": score_hits(hits), "summary": summarize_hits(hits)})
    out.sort(key=lambda c: (-c["summary"]["air_sweeper"], -c["score"],
                            -len(c["hits"]), c["from"][0], c["from"][1]))
    return out


def optimize_giant_arrow(layout, grid=44, tol=1.2, top=5):
    """返回按评分排序的候选箭线；best 为最高分（无对空目标时为空）。"""
    cands = candidate_arrow_lines(layout, grid=grid, tol=tol)
    return {"best": cands[0] if cands else None, "candidates": cands[:int(top)]}


TESLA_WARNING = "⚠ 特斯拉默认不现形：图中格位仅为推测；其 DPS 低，穿云箭收益低"


def tesla_warning(layout):
    """布局里有隐形特斯拉时返回提醒文案，否则返回空串。"""
    for b in (layout or {}).get("buildings") or []:
        if isinstance(b, dict) and b.get("type") in HIDDEN_TYPES:
            return TESLA_WARNING
    return ""
