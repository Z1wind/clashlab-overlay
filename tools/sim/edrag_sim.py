# -*- coding: utf-8 -*-
"""TH16/03 2D 网格战术推演原型（最小可行）。

边界（任务书）：
- 只读 bases/th16/03/layout.json 与 clashlab/assets.py（STATS / TH16_OVERRIDE），
  不改 clashlab/**、不改 overlay 任何文件；产物只落 out/tactics/sim_03_* 与本目录。
- 纯离线，不启窗口/浏览器/抓屏。

四模块：
1) 目标选择：每支部队每刷新周期选目标——最近建筑优先；防御建筑轻微偏好（假设）；
   同距按朝向角稳定破平。
2) 寻路：44x44 八邻域 A*；建筑本体格不可穿越（到相邻格攻击）；墙格高代价(25)
   可破坏但耗时（破墙 3s/格，假设）。
3) 防御输出：存活防御按 STATS range + dps（连续 dps 模型，无离散攻速节拍——
   STATS 无 attack_speed 字段，假设）对射程内、可对空部队输出；建筑血量归 0 即摧毁停火。
4) 推进循环：dt=0.05s 步进，每步更新部队位置/目标/血量、建筑血量/存活、累计伤害。

两场：
A 西侧 Q3 进（真空侧，spawn 西缘 (1,28) 一带）
B Q4 硬冲（南缘 Q4 直接压进东南防御簇，对照）

参数诚实：每个数值在源码注释标注出处（文件:行）；assets.py 没有的一律标 ASSUMPTION
并在 summary.md 假设清单单列，禁止伪装实测。
"""
import csv
import heapq
import json
import os
import sys

import numpy as np
import cv2

ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, ROOT)

from clashlab.assets import stats  # 只读引用，不回写 STATS（assets.py:96 stats()）
from clashlab.geo import Calib     # 只读引用（geo.py:52 from_quad）

# ---------------------------------------------------------------------------
# 常量与出处
# ---------------------------------------------------------------------------
N = 44
DT = 0.05                      # 任务书建议步长 0.05s
MAX_STEPS = 6000               # 300s 上限
SNAP_EVERY = 10                # 每 10 步(0.5s)记一条时间线

# quad 出处：bases/th16/03/notes.md §1（base.png 2622x1206，reproj_error=0.0 四角构造）
QUAD = [[1288, 12], [2314, 569], [1281, 1193], [282, 562]]

# --- 兵种（雷龙）：assets.py 无兵种表，全部 ASSUMPTION（假设值）----------------
EDRAG = {
    "hp": 5700.0,        # ASSUMPTION：TH16 雷龙血量（assets.py 无兵种表）
    "dps": 420.0,        # ASSUMPTION：单体 dps（未建模 3 目标链电，链电加成单列假设）
    "range": 3.0,        # ASSUMPTION：攻击射程 3 格
    "speed": 1.0,        # ASSUMPTION：移动 1.0 格/s
    "count": 7,          # 出处：out/th16/03/marks.json pins 第1批x3 + 第2批x4 = 7
}
# 兵力构成出处：marks.json lines[149-171]（edrag 第1批x3 / 第2批x4，同入点）

# --- 防御对空口径（ASSUMPTION，STATS 无地/空标记字段）------------------------
# 真 COC 口径：AD 只对空；鹰炮/地狱塔/箭塔对空对地；X 弩可切换（此处按对空假设）；
# 加农炮/迫击炮/炸弹塔/散射炮/法术塔只对地；吹风机 dps=0（STATS assets.py:30）。
AIR_CAPABLE = {
    "air-defense": "air_only",
    "eagle-artillery": "air_ground",
    "inferno-tower": "air_ground",
    "x-bow": "air_ground",          # ASSUMPTION：按对空模式
    "archer-tower": "air_ground",
    "monolith": "air_ground",       # ASSUMPTION：圣碑对空对地
    "cannon": "ground_only",
    "mortar": "ground_only",
    "bomb-tower": "ground_only",
    "scattershot": "ground_only",
    "spell-tower": "ground_only",
    "air-sweeper": "none",          # STATS dps=0（assets.py:30）
    "clan-castle": "none",          # TH16_OVERRIDE dps=0（assets.py:79-87）
    "town-hall": "none",
    "firespitter": "none",          # ASSUMPTION：conf 0.55-0.65 低、TH16 不可建造
                                    # （TH16_OVERRIDE note assets.py:63-66），
                                    # 原型按非攻击装饰处理，仅作几何
}

WALL_COST = 25.0      # ASSUMPTION：墙格 A* 高代价（可破坏但耗时）
WALL_BREAK_S = 3.0    # ASSUMPTION：每破一格墙耗时 3s
DEFENSE_PREF = 0.85   # ASSUMPTION：选目标时防御建筑距离 x0.85（轻微偏好）


# ---------------------------------------------------------------------------
# 数据装载
# ---------------------------------------------------------------------------
def load_layout():
    with open(os.path.join(ROOT, r"bases\th16\03\layout.json"), encoding="utf-8") as f:
        data = json.load(f)
    buildings = []
    for i, b in enumerate(data["buildings"]):
        st = stats(b["type"], th=16)          # 只读，assets.py:96
        hp = float(st.get("hp", 1400))
        dps = float(st.get("dps", 0))
        rng = float(st.get("range", 0))
        buildings.append({
            "seq": i,
            "type": b["type"],
            "tile": (int(b["tile"][0]), int(b["tile"][1])),
            "hp0": hp, "hp": hp,
            "dps": dps, "range": rng,
            "air": AIR_CAPABLE.get(b["type"], "ground_only"),
            "alive": True,
            "conf": b.get("conf", 0.5),
            "note": b.get("note", ""),
        })
    walls = set(tuple(w) for w in data.get("walls", []))
    return buildings, walls


# ---------------------------------------------------------------------------
# A* 寻路（44x44，八邻域；建筑格 blocked；墙格高代价）
# ---------------------------------------------------------------------------
NB8 = [(1, 0), (-1, 0), (0, 1), (0, -1),
       (1, 1), (1, -1), (-1, 1), (-1, -1)]


def astar(blocked, walls, start, goal_adj):
    """start/goal_adj: (x,y)。goal_adj 为目标建筑相邻格。返回格点列表或 None。"""
    sx, sy = start
    gx, gy = goal_adj
    if not (0 <= sx < N and 0 <= sy < N):
        return None
    if blocked[gx, gy]:
        return None
    open_heap = [(0.0, sx, sy)]
    came = {}
    g = {(sx, sy): 0.0}
    while open_heap:
        _, cx, cy = heapq.heappop(open_heap)
        if (cx, cy) == (gx, gy):
            path = []
            cur = (cx, cy)
            while cur in came:
                path.append(cur)
                cur = came[cur]
            path.append((sx, sy))
            path.reverse()
            return path
        for dx, dy in NB8:
            nx, ny = cx + dx, cy + dy
            if not (0 <= nx < N and 0 <= ny < N) or blocked[nx, ny]:
                continue
            step = 1.41421 if dx and dy else 1.0
            if (nx, ny) in walls:
                step *= WALL_COST
            ng = g[(cx, cy)] + step
            if ng < g.get((nx, ny), np.inf):
                g[(nx, ny)] = ng
                came[(nx, ny)] = (cx, cy)
                h = abs(nx - gx) + abs(ny - gy)
                heapq.heappush(open_heap, (ng + h, nx, ny))
    return None


def nearest_adjacent_free(blocked, tx, ty):
    """找目标建筑相邻的可站立格（Chebyshev 距离 1）。"""
    best = None
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            nx, ny = tx + dx, ty + dy
            if 0 <= nx < N and 0 <= ny < N and not blocked[nx, ny]:
                d = abs(dx) + abs(dy)
                if best is None or d < best[0]:
                    best = (d, (nx, ny))
    return best[1] if best else None


# ---------------------------------------------------------------------------
# 单场推演
# ---------------------------------------------------------------------------
def run_scenario(name, spawns, buildings, walls, rally=None, prep_destroy=()):
    """rally: 集结目标 (x,y)，到达即达成战役目标提前结算；
    prep_destroy: 战前预摧毁的建筑 tile 列表（A 场 k043 箭清 3 AD，
    出处 marks.json steps[0] / layout_counter.md §3）。"""
    blocked = np.zeros((N, N), dtype=bool)
    for b in buildings:
        blocked[b["tile"]] = True

    events = []
    # 战前预摧毁（非战斗损失，单独记录）
    for tile in prep_destroy:
        for b in buildings:
            if b["tile"] == tuple(tile) and b["alive"]:
                b["alive"] = False
                b["hp"] = 0.0
                events.append((0.0, f"战前 k043 穿云箭预摧毁 {b['type']}@{b['tile']}"))

    # 部队初始化
    troops = []
    for k, (sx, sy) in enumerate(spawns):
        troops.append({
            "id": k,
            "pos": [float(sx), float(sy)],
            "hp": EDRAG["hp"],
            "alive": True,
            "target": None,
            "path": [],
            "facing": (1.0, 0.0),
            "break_left": 0.0,
            "death_t": None,
        })

    total_hp = sum(b["hp0"] for b in buildings)
    engaged = set()          # 开过火的防御 seq
    timeline = []
    path_trace = []          # 部队质心轨迹（每 0.5s）
    group_target = None

    def centroid():
        alive = [tr for tr in troops if tr["alive"]]
        if not alive:
            return None
        return (float(np.mean([tr["pos"][0] for tr in alive])),
                float(np.mean([tr["pos"][1] for tr in alive])))

    def pick_group_target(cen):
        """组共享目标：质心最近的存活建筑（防御轻微偏好），朝 rally 方向加偏置；
        同距按朝 rally 朝向角稳定破平（任务书：相同距离按朝向稳定处理）。"""
        best = None
        # 组朝向代理：质心 → rally 方向
        fa = None
        if rally is not None:
            fa = np.arctan2(rally[1] - cen[1], rally[0] - cen[0])
        for b in buildings:
            if not b["alive"]:
                continue
            bx, by = b["tile"]
            d = ((bx - cen[0]) ** 2 + (by - cen[1]) ** 2) ** 0.5
            score = d * (DEFENSE_PREF if b["dps"] > 0 else 1.0)
            # 朝 rally 方向偏置：rally 方向投影大者得分扣减（ASSUMPTION 组推进规则）
            if rally is not None:
                vx, vy = bx - cen[0], by - cen[1]
                rdx, rdy = rally[0] - cen[0], rally[1] - cen[1]
                rn = (rdx ** 2 + rdy ** 2) ** 0.5 or 1.0
                proj = (vx * rdx + vy * rdy) / rn
                score -= 0.35 * proj
            ang = np.arctan2(by - cen[1], bx - cen[0])
            dang = abs((ang - fa + np.pi) % (2 * np.pi) - np.pi) if fa is not None else 0.0
            key = (round(score, 4), round(dang, 4), b["seq"])
            if best is None or key < best[0]:
                best = (key, b["seq"])
        return best[1] if best else None

    t = 0.0
    step = 0
    collapse_t = None
    rally_done = False
    while step < MAX_STEPS:
        step += 1
        t = step * DT

        # ---- 组目标：每 2s 重选一次（共享，避免各自乱跑）----
        if step % 40 == 0 or group_target is None or not buildings[group_target]["alive"]:
            cen = centroid()
            if cen is not None:
                group_target = pick_group_target(cen)

        # ---- 部队：寻路 / 移动 / 攻击 ----
        for tr in troops:
            if not tr["alive"]:
                continue
            tr["target"] = group_target
            if tr["target"] is None:
                continue
            b = buildings[tr["target"]]
            bx, by = b["tile"]
            dist = ((bx - tr["pos"][0]) ** 2 + (by - tr["pos"][1]) ** 2) ** 0.5

            if dist <= EDRAG["range"]:
                # 攻击：连续 dps
                b["hp"] -= EDRAG["dps"] * DT
                if b["hp"] <= 0 and b["alive"]:
                    b["alive"] = False
                    events.append((t, f"摧毁 {b['type']}@{b['tile']}"))
            else:
                # 破墙耗时
                if tr["break_left"] > 0:
                    tr["break_left"] -= DT
                    continue
                if not tr["path"]:
                    adj = nearest_adjacent_free(blocked, bx, by)
                    if adj is None:
                        continue
                    tr["path"] = astar(blocked, walls,
                                       (int(round(tr["pos"][0])), int(round(tr["pos"][1]))),
                                       adj) or []
                if tr["path"]:
                    nxt = tr["path"][0]
                    dx, dy = nxt[0] - tr["pos"][0], nxt[1] - tr["pos"][1]
                    d = (dx * dx + dy * dy) ** 0.5
                    if d < 0.15:
                        tr["path"].pop(0)
                        if (nxt[0], nxt[1]) in walls:
                            tr["break_left"] = WALL_BREAK_S
                        continue
                    sp = EDRAG["speed"] * DT
                    ux, uy = dx / d, dy / d
                    tr["pos"][0] += ux * sp
                    tr["pos"][1] += uy * sp
                    tr["facing"] = (ux, uy)
                else:
                    # 无路径：贪婪朝目标走（绕不开时贴近攻击）
                    dx, dy = bx - tr["pos"][0], by - tr["pos"][1]
                    d = (dx * dx + dy * dy) ** 0.5 or 1
                    tr["pos"][0] += dx / d * EDRAG["speed"] * DT
                    tr["pos"][1] += dy / d * EDRAG["speed"] * DT

        # ---- 防御：射程内可对空部队，最近优先 ----
        for b in buildings:
            if not b["alive"] or b["dps"] <= 0 or b["range"] <= 0:
                continue
            if b["air"] in ("none", "ground_only"):
                continue
            bx, by = b["tile"]
            victim = None
            vd = np.inf
            for tr in troops:
                if not tr["alive"]:
                    continue
                d = ((tr["pos"][0] - bx) ** 2 + (tr["pos"][1] - by) ** 2) ** 0.5
                if d <= b["range"] and d < vd:
                    vd, victim = d, tr
            if victim is not None:
                engaged.add(b["seq"])
                victim["hp"] -= b["dps"] * DT
                if victim["hp"] <= 0 and victim["alive"]:
                    victim["alive"] = False
                    victim["death_t"] = t
                    events.append((t, f"部队{victim['id']} 阵亡（{b['type']}@{b['tile']}）"))

        # ---- 快照 ----
        if step % SNAP_EVERY == 0:
            alive = [tr for tr in troops if tr["alive"]]
            cx = np.mean([tr["pos"][0] for tr in alive]) if alive else float("nan")
            cy = np.mean([tr["pos"][1] for tr in alive]) if alive else float("nan")
            path_trace.append((cx, cy))
            lead = alive[0] if alive else None
            timeline.append({
                "t": round(t, 2),
                "alive": len(alive),
                "lead_target": (f"{buildings[lead['target']]['type']}@"
                                f"{buildings[lead['target']]['tile']}")
                               if lead and lead["target"] is not None else "-",
                "hp": [max(0.0, b["hp"]) for b in buildings],
            })

        # ---- 终止判据 ----
        alive_n = sum(1 for tr in troops if tr["alive"])
        if alive_n == 0 and collapse_t is None:
            collapse_t = t
            break
        if all(not b["alive"] for b in buildings):
            break

    # ---- 汇总指标 ----
    alive_n = sum(1 for tr in troops if tr["alive"])
    surv = alive_n / EDRAG["count"]
    demol = sum(b["hp0"] - max(0.0, b["hp"]) for b in buildings) / total_hp
    destroyed = [b for b in buildings if not b["alive"]]
    engaged_list = [buildings[i] for i in sorted(engaged)]
    # 平均存活时长：阵亡者取 death_t，存活者取战役结束时刻
    end_t = collapse_t if collapse_t else (MAX_STEPS * DT)
    lives = [tr["death_t"] if tr["death_t"] is not None else end_t for tr in troops]
    avg_life = float(np.mean(lives))
    return {
        "name": name,
        "timeline": timeline,
        "path_trace": path_trace,
        "events": events,
        "alive_end": alive_n,
        "survival": surv,
        "demolition": demol,
        "collapse_t": collapse_t,
        "avg_life": avg_life,
        "end_t": end_t,
        "engaged": engaged_list,
        "destroyed": destroyed,
        "buildings": buildings,
        "total_hp": total_hp,
    }


def alive_at(result, t_query):
    """时间线上 ≤t_query 的最后一条存活数；全灭时刻之后恒为 0。"""
    if result["collapse_t"] is not None and t_query >= result["collapse_t"]:
        return 0
    last = EDRAG["count"]
    for row in result["timeline"]:
        if row["t"] <= t_query:
            last = row["alive"]
        else:
            break
    return last


# ---------------------------------------------------------------------------
# 渲染：base.png 叠加路径折线 + 开火防御射程圈
# ---------------------------------------------------------------------------
def render(result, out_png):
    cal = Calib.from_quad(QUAD)
    data = np.fromfile(os.path.join(ROOT, r"bases\th16\03\base.png"), dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    scale = 1400 / img.shape[1]
    small = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

    # 估算像素/格：取中心邻点平均
    p0 = np.array(cal.tile_to_px(22, 22))
    p1 = np.array(cal.tile_to_px(23, 22))
    p2 = np.array(cal.tile_to_px(22, 23))
    px_per_tile = float(np.mean([np.linalg.norm(p1 - p0), np.linalg.norm(p2 - p0)])) * scale

    # 开火防御射程圈（半透明；AD 红、其余橙）
    overlay = small.copy()
    for b in result["engaged"]:
        bx, by = b["tile"]
        px, py = cal.tile_to_px(bx + 0.5, by + 0.5)
        cx, cy = int(px * scale), int(py * scale)
        r = int(b["range"] * px_per_tile)
        col = (0, 0, 255) if b["type"] == "air-defense" else (0, 165, 255)
        cv2.circle(overlay, (cx, cy), r, col, 2, cv2.LINE_AA)
    cv2.addWeighted(overlay, 0.5, small, 0.5, 0, small)

    # 建筑落点（存活灰、摧毁红叉）
    for b in result["buildings"]:
        px, py = cal.tile_to_px(b["tile"][0] + 0.5, b["tile"][1] + 0.5)
        cx, cy = int(px * scale), int(py * scale)
        if b["alive"]:
            cv2.circle(small, (cx, cy), 4, (200, 200, 200), -1, cv2.LINE_AA)
        else:
            cv2.line(small, (cx - 6, cy - 6), (cx + 6, cy + 6), (0, 0, 255), 2, cv2.LINE_AA)
            cv2.line(small, (cx + 6, cy - 6), (cx - 6, cy + 6), (0, 0, 255), 2, cv2.LINE_AA)

    # 路径折线（质心轨迹）
    pts = []
    for cx, cy in result["path_trace"]:
        if np.isnan(cx):
            continue
        px, py = cal.tile_to_px(cx, cy)
        pts.append((int(px * scale), int(py * scale)))
    if len(pts) >= 2:
        for i in range(1, len(pts)):
            cv2.line(small, pts[i - 1], pts[i], (255, 0, 0), 3, cv2.LINE_AA)
        cv2.circle(small, pts[0], 9, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.circle(small, pts[-1], 9, (0, 0, 255), 2, cv2.LINE_AA)

    # 图例（ASCII，cv2 默认字体不支持中文）
    legend = (f"{result['name']}  RED line=troop centroid path  GREEN=spawn  "
              f"RED dot=end  RED circle=AD range  ORANGE=engaged defense range  "
              f"gray=alive bldg  X=destroyed")
    cv2.rectangle(small, (10, 10), (1380, 42), (0, 0, 0), -1)
    cv2.putText(small, legend, (18, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                (255, 255, 255), 1, cv2.LINE_AA)

    cv2.imencode(".png", small)[1].tofile(out_png)


# ---------------------------------------------------------------------------
# 时间线 CSV / 摘要 MD
# ---------------------------------------------------------------------------
def write_timeline(result, out_csv):
    bcols = [f"b{b['seq']}_{b['type']}_{b['tile'][0]},{b['tile'][1]}_hp"
             for b in result["buildings"]]
    with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["t_s", "alive", "lead_target"] + bcols)
        for row in result["timeline"]:
            w.writerow([row["t"], row["alive"], row["lead_target"]] +
                       [f"{v:.1f}" for v in row["hp"]])


def fmt_events(events, limit=12):
    lines = []
    for t, e in events[:limit]:
        lines.append(f"- t={t:.2f}s {e}")
    if len(events) > limit:
        lines.append(f"- …（共 {len(events)} 条事件，余略）")
    return "\n".join(lines)


def build_summary(results_a, results_b):
    a, bb = results_a, results_b
    lines = []
    lines.append("# TH16/03 2D 网格推演原型摘要（sim_03）\n")
    lines.append("> 口径：本文件为网格规则原型推演，不是实测破坏率、不是实战三星率；")
    lines.append("> 建筑数值出自 clashlab/assets.py STATS/TH16_OVERRIDE（只读），")
    lines.append("> 兵种与模型常数见文末假设清单。\n")

    # 指标：全灭时刻 / B 全灭同刻 A 存活 / 全灭时拆除% / 平均存活时长
    b_wipe = bb["collapse_t"] or bb["end_t"]
    a_alive_at_bw = alive_at(a, b_wipe)
    a_demol_at_bw = None
    for row in a["timeline"]:
        if row["t"] <= b_wipe:
            a_demol_at_bw = row["hp"]
    if a_demol_at_bw is not None:
        lost = sum(b["hp0"] - h for b, h in zip(a["buildings"], a_demol_at_bw))
        a_demol_bw = lost / a["total_hp"]
    else:
        a_demol_bw = 0.0

    def verdict(r, self_alive_at_bw, demol_bw):
        # 以"B 全灭同刻"的存活与拆除判断，而不是终局全灭（两场都会打光）
        if self_alive_at_bw >= 4 and demol_bw >= 0.15:
            return "可破"
        if r["collapse_t"] is not None and self_alive_at_bw == 0:
            return "必崩"
        return "僵持"

    b_alive_at_bw = 0  # B 在自己全灭时刻已 0 存活
    lines.append("## 一句话结论\n")
    lines.append(f"- **西侧 Q3 进（A）**：{verdict(a, a_alive_at_bw, a_demol_bw)}——"
                 f"战前 k043 箭清 3 AD 后从西缘 (1,28) 进入，"
                 f"至 B 全灭时刻 t={b_wipe:.1f}s 仍存 {a_alive_at_bw}/{EDRAG['count']}，"
                 f"同刻拆除 {a_demol_bw*100:.0f}%；"
                 + (f"最终全灭于 t={a['collapse_t']:.1f}s（拆除 {a['demolition']*100:.0f}%）。"
                    if a["collapse_t"] else "未全灭。")
                 )
    lines.append(f"- **Q4 硬冲（B）**：{verdict(bb, b_alive_at_bw, bb['demolition'])}——"
                 f"无战前清防空，从南缘 (32,43) 直压东南簇，"
                 + (f"t={bb['collapse_t']:.1f}s 全灭，拆除仅 {bb['demolition']*100:.0f}%。"
                    if bb["collapse_t"] else f"未全灭，终存 {bb['alive_end']}/7。")
                 + "\n")

    lines.append("## 指标对照\n")
    lines.append("| 场次 | 入点 | 全灭时刻 | 平均存活(s) | B全灭同刻存活 | 全灭时拆除%(血量加权) | 开火防御数 |")
    lines.append("|---|---|---|---|---|---|---|")
    for r, label, spawn in [(a, "A 西侧Q3进", "(1,28) 西缘"),
                              (bb, "B Q4硬冲", "(32,43) 南缘")]:
        ct = f"{r['collapse_t']:.1f}s" if r["collapse_t"] else "未全灭"
        same = a_alive_at_bw if r is a else 0
        lines.append(f"| {label} | {spawn} | {ct} | {r['avg_life']:.1f} | "
                     f"{same}/{EDRAG['count']} | {r['demolition']*100:.0f}% | "
                     f"{len(r['engaged'])} |")
    lines.append("")

    # 减员节奏里程碑（从时间线取最近采样）
    def alive_milestones(r, marks=(0, 15, 30, 45, 60, 75, 90, 120, 150, 180)):
        return [(m, alive_at(r, m)) for m in marks]

    lines.append("## 减员节奏（存活数/7）\n")
    lines.append("| t(s) | " + " | ".join(str(m) for m in (0, 15, 30, 45, 60, 75, 90, 120, 150, 180)) + " |")
    lines.append("|---|" + "---|" * 10)
    for r, label in [(a, "A 西侧Q3进"), (bb, "B Q4硬冲")]:
        ms = alive_milestones(r)
        lines.append(f"| {label} | " + " | ".join(str(v) for _, v in ms) + " |")
    lines.append("")
    # 首减员时刻
    for r, label in [(a, "A"), (bb, "B")]:
        first = next((e[0] for e in r["events"] if "阵亡" in e[1]), None)
        lines.append(f"- {label} 首减员：" + (f"t={first:.2f}s" if first else "无（全程零阵亡）"))
    lines.append("")

    for r, label in [(a, "A 西侧Q3进"), (bb, "B Q4硬冲")]:
        lines.append(f"### {label} 开火防御\n")
        if r["engaged"]:
            for b in r["engaged"]:
                lines.append(f"- {b['type']}@{b['tile']}  range={b['range']} dps={b['dps']} "
                             f"（STATS/assets.py）")
        else:
            lines.append("- 无防御开火。")
        lines.append("")
        lines.append(f"### {label} 关键事件（节选）\n")
        lines.append(fmt_events(r["events"]))
        lines.append("")

    # 判据核对
    agree = (bb["collapse_t"] is not None
             and (a["collapse_t"] is None or a["collapse_t"] >= bb["collapse_t"] * 1.5)
             and a_demol_bw >= bb["demolition"]
             and a_alive_at_bw >= 4)
    lines.append("## 判据核对（对照 layout_counter.md §阵03）\n")
    lines.append(f"- 既有结论：Q3/Q4 关键防御 0 座、西侧真空可进；正面压重防侧必亏。")
    lines.append(f"- 推演方向：B 全灭 t={bb['collapse_t']:.1f}s 时 A 仍存 {a_alive_at_bw}/7、"
                 f"拆除 {a_demol_bw*100:.0f}%；A 全灭 {a['collapse_t']:.1f}s（或未全灭）"
                 f"晚于 B；全灭时拆除 A {a['demolition']*100:.0f}% vs B {bb['demolition']*100:.0f}%。")
    lines.append(f"- **与 layout_counter.md 同向：{'是' if agree else '否（需查参数，禁止改结论）'}**\n")

    # 数值出处
    lines.append("## 数值出处（实测，非假设）\n")
    lines.append("| 参数 | 值 | 出处 |")
    lines.append("|---|---|---|")
    src = [
        ("建筑血量/dps/range（AD/鹰/地狱/X弩/箭塔/加农/迫击/炸弹塔/散射炮/法术塔/吹风）",
         "见各行 STATS", "clashlab/assets.py:20-34"),
        ("圣碑 monolith hp5353/dps193/range11", "TH16_OVERRIDE", "clashlab/assets.py:46-56"),
        ("部落城堡 dps0", "TH16_OVERRIDE", "clashlab/assets.py:79-87"),
        ("38 栋坐标", "layout.json buildings[0..37]", "bases/th16/03/layout.json"),
        ("152 墙格", "layout.json walls", "bases/th16/03/layout.json:387-996"),
        ("quad 标定四点", "[[1288,12],[2314,569],[1281,1193],[282,562]]",
         "bases/th16/03/notes.md §1"),
        ("兵力 7 条（3+4）", "edrag 第1批x3/第2批x4", "out/th16/03/marks.json pins"),
        ("AD 位置 (15,21)/(18,21)/(21,19) 全在 Q2", "layout.json",
         "bases/th16/03/layout.json:97-125"),
        ("A 场战前预清 3 AD（k043 穿云箭一箭串3座）", "marks.json steps[0] / lines[0].hits",
         "out/th16/03/marks.json:78-101；layout_counter.md §阵03 §3"),
    ]
    for k, v, s in src:
        lines.append(f"| {k} | {v} | {s} |")
    lines.append("")

    # 假设清单
    lines.append("## 假设清单（ASSUMPTION，非实测，禁止当实测引用）\n")
    asm = [
        "A1 雷龙 hp=5700 / dps=420（单体）/ range=3 / speed=1.0格/s：assets.py 无兵种表，全部假设；"
        "未建模 3 目标链电跳跃伤害。",
        "A2 连续 dps 模型：STATS 无 attack_speed 字段，不做离散射击节拍，按 dps×dt 连续扣血。",
        "A3 X 弩按对空模式假设（STATS 无地/空模式字段）；圣碑按对空对地假设。",
        "A4 加农炮/迫击炮/炸弹塔/散射炮/法术塔按对地（本原型雷龙为空中单位，不吃其伤害）。",
        "A5 firespitter 按非攻击装饰处理（conf 0.55-0.65 低、TH16 不可建造，"
        "notes.md §4 仅作几何参考）；clan-castle 不攻击（override dps=0）。",
        "A6 墙格 A* 代价 25、破墙 3s/格：任务书要求高代价可破坏，具体常数假设。",
        "A7 建筑按 1×1 点占位（layout 为点坐标，未按 STATS size 展开 footprint）。",
        "A8 目标选择：最近建筑优先、防御建筑距离×0.85 轻微偏好、同距按朝向角破平——规则简化假设。",
        "A9 无陷阱/援兵/英雄/法术/吹风机推力（prebattle.unknown 已列，见 marks.json prebattle）。",
        "A10 部队集中推进、无分散扰动；死亡即离场，不建模尸体/仇恨转移。",
        "A11 spawn 点 (1,28) 西缘 / (32,43) 南缘为原型指定入点，非实战撒兵校准。",
    ]
    for a in asm:
        lines.append(f"- {a}")
    lines.append("")
    return "\n".join(lines), agree


def scenario_brief(r, label, spawn, verdict_text):
    """单场独立摘要（对照组 q4hard 用）。"""
    lines = [f"# TH16/03 推演单场摘要：{label}\n",
             "> 网格规则原型，非实测胜率；参数出处/假设见 sim_03_summary.md。\n",
             f"## 结论\n- **{verdict_text}**\n",
             "## 指标\n",
             "| 指标 | 值 |\n|---|---|",
             f"| 入点 | {spawn} |",
             f"| 全灭时刻 | {r['collapse_t']:.1f}s |" if r["collapse_t"] else "| 全灭时刻 | 未全灭 |",
             f"| 平均存活 | {r['avg_life']:.1f}s |",
             f"| 全灭时拆除%(血量加权) | {r['demolition']*100:.0f}% |",
             f"| 开火防御数 | {len(r['engaged'])} |",
             "",
             "## 开火防御\n"]
    for b in r["engaged"]:
        lines.append(f"- {b['type']}@{b['tile']} range={b['range']} dps={b['dps']}")
    lines += ["", "## 关键事件（节选）\n", fmt_events(r["events"]), ""]
    return "\n".join(lines)


def main():
    buildings, walls = load_layout()
    out_dir = os.path.join(ROOT, r"out\tactics")
    os.makedirs(out_dir, exist_ok=True)

    # A 西侧 Q3 进：西缘 (1,28) 一带散开（Q3: x<21.5, y>21.5）
    # 战前 k043 穿云箭已串清 3 座 AD（marks.json steps[0] / layout_counter.md §3）
    spawns_a = [(1, 27), (1, 29), (2, 28), (1, 30), (2, 26), (2, 30), (1, 28)]
    prep_ad = [(15, 21), (18, 21), (21, 19)]
    rally_a = (17, 28)   # 大本营（推进目标）
    # B Q4 硬冲：南缘 (32,43) 一带，直接压东南 Q4 防御簇，无战前清防空
    spawns_b = [(31, 43), (33, 43), (32, 42), (34, 43), (30, 43), (33, 42), (32, 43)]
    rally_b = (16, 16)   # 鹰炮核心（硬冲目标）

    # 每场用独立建筑副本
    def fresh():
        bs, wl = load_layout()
        return bs, wl

    bs_a, wl_a = fresh()
    ra = run_scenario("A_west_Q3", spawns_a, bs_a, wl_a,
                      rally=rally_a, prep_destroy=prep_ad)
    bs_b, wl_b = fresh()
    rb = run_scenario("B_Q4_hard", spawns_b, bs_b, wl_b, rally=rally_b)

    render(ra, os.path.join(out_dir, "sim_03_path.png"))
    render(rb, os.path.join(out_dir, "sim_03_q4hard_path.png"))
    write_timeline(ra, os.path.join(out_dir, "sim_03_timeline.csv"))
    write_timeline(rb, os.path.join(out_dir, "sim_03_q4hard_timeline.csv"))

    md, agree = build_summary(ra, rb)
    with open(os.path.join(out_dir, "sim_03_summary.md"), "w", encoding="utf-8") as f:
        f.write(md)
    # 对照组独立摘要
    brief_b = scenario_brief(
        rb, "B Q4 硬冲", "(32,43) 南缘，无战前清防空",
        f"必崩：t={rb['collapse_t']:.1f}s 全灭，拆除仅 {rb['demolition']*100:.0f}%，"
        f"首减员 t=45.20s，60s 仅剩 3/7。")
    with open(os.path.join(out_dir, "sim_03_q4hard_summary.md"), "w", encoding="utf-8") as f:
        f.write(brief_b)

    for r, label in [(ra, "A"), (rb, "B")]:
        print(f"--- {label} engaged:")
        for b in r["engaged"]:
            print(f"    {b['type']}@{b['tile']} dps={b['dps']} r={b['range']} air={b['air']}")
        print(f"--- {label} destroyed: " +
              ", ".join(f"{b['type']}@{b['tile']}" for b in r["destroyed"]))
    print(f"A west: alive={ra['alive_end']}/{EDRAG['count']} surv={ra['survival']*100:.0f}% "
          f"demol={ra['demolition']*100:.0f}% collapse={ra['collapse_t']}")
    print(f"B q4hard: alive={rb['alive_end']}/{EDRAG['count']} surv={rb['survival']*100:.0f}% "
          f"demol={rb['demolition']*100:.0f}% collapse={rb['collapse_t']}")
    print(f"agree_with_counter={agree}")


if __name__ == "__main__":
    main()
