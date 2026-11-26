# -*- coding: utf-8 -*-
"""TH16 阵型标注工具核心逻辑 —— 纯标准库（不依赖 numpy / cv2 / 任何第三方包）。

被两处复用：
  - tools/annotate/start.py  本地 HTTP 服务（读写 / API）
  - tools/annotate/index.html 由服务端把 H / Hinv / 调色板 / 预填数据下发，前端只做矩阵乘法
  - tests/test_annotate.py   纯逻辑单测（坐标换算 / schema / 存取 / 预填差异 / 发现）

坐标约定（与 clashlab/geo.py、clashlab/topdown.py 一致，勿翻转）：
  - tile 原点 (0,0) = 地图菱形最上顶点；gx 沿「顶点→右腰」(右下)，gy 沿「顶点→左腰」(左下)；
  - quad 顺序 = 上、右、下、左，对应 tile (0,0)/(grid,0)/(grid,grid)/(0,grid)，单位是 base.png 原图像素；
  - layout.json 的整数 tile 是**单元格索引**，单元格中心 = (tile + 0.5)（topdown.py 即按此渲染），
    因此像素 → tile 用 floor（不是 round），否则会把中心 +0.5 半格算成下一格。
"""
from __future__ import annotations

import datetime
import json
import math
import os
import re
import struct
import tempfile

# ---------------------------------------------------------------------------
# 常量：调色板 / schema
# ---------------------------------------------------------------------------

GRID_DEFAULT = 44
PALETTE_HOTKEY_COUNT = 9          # 数字键 1..9 对应 PALETTE 前 9 项
OUT_DIR_REL = os.path.join("out", "annotate")
SUMMARY_NAME = "summary.json"
SUMMARY_TOOL = "tools/annotate"
ANNOTATE_SCHEMA = 1

# 调色板顺序 = UI 顺序：前 9 个吃数字键，其后放其它防御/资源建筑。
PALETTE = [
    # 1..9 常用防御
    "cannon", "archer-tower", "mortar", "wizard-tower", "air-defense",
    "x-bow", "inferno-tower", "hidden-tesla", "air-sweeper",
    # 其它防御 / 核心
    "town-hall", "clan-castle", "eagle-artillery", "scattershot", "monolith",
    "spell-tower", "bomb-tower", "multi-archer-tower", "ricochet-cannon", "firespitter",
    # 资源 / 兵营（补录漏标时用）
    "gold-storage", "elixir-storage", "dark-elixir-storage",
    "gold-mine", "elixir-collector", "dark-elixir-drill",
    "barracks", "dark-barracks", "army-camp", "laboratory",
    "spell-factory", "dark-spell-factory", "builder-hut",
]
ALLOWED_TYPES = frozenset(PALETTE)

TYPE_CN = {
    "cannon": "加农炮", "archer-tower": "箭塔", "mortar": "迫击炮",
    "wizard-tower": "法师塔", "air-defense": "防空", "x-bow": "X连弩",
    "inferno-tower": "地狱塔", "hidden-tesla": "特斯拉", "air-sweeper": "吹风机",
    "town-hall": "大本营", "clan-castle": "部落城堡", "eagle-artillery": "鹰火炮",
    "scattershot": "散射炮", "monolith": "方尖碑", "spell-tower": "法术塔",
    "bomb-tower": "炸弹塔", "multi-archer-tower": "多重箭塔",
    "ricochet-cannon": "弹射加农炮", "firespitter": "喷火器",
    "gold-storage": "金币仓库", "elixir-storage": "圣水仓库",
    "dark-elixir-storage": "黑油仓库", "gold-mine": "金矿",
    "elixir-collector": "圣水收集器", "dark-elixir-drill": "黑油钻井",
    "barracks": "兵营", "dark-barracks": "暗黑兵营", "army-camp": "训练营",
    "laboratory": "实验室", "spell-factory": "法术工厂",
    "dark-spell-factory": "暗黑法术工厂", "builder-hut": "建筑工人小屋",
}

# 仅用于网页上画框（视觉尺寸），不参与 schema / 坐标换算。
TYPE_SIZE_DEFAULT = 3
TYPE_SIZE = {
    "town-hall": 4,
    "inferno-tower": 2, "hidden-tesla": 2, "air-sweeper": 2, "spell-tower": 2,
    "builder-hut": 2, "dark-elixir-drill": 2,
    "eagle-artillery": 3, "scattershot": 3, "monolith": 3, "clan-castle": 3,
    "x-bow": 3, "cannon": 3, "archer-tower": 3, "wizard-tower": 3, "air-defense": 3,
    "mortar": 3, "bomb-tower": 3, "multi-archer-tower": 3, "ricochet-cannon": 3,
    "firespitter": 3, "gold-storage": 3, "elixir-storage": 3, "dark-elixir-storage": 3,
    "gold-mine": 3, "elixir-collector": 3, "barracks": 3, "dark-barracks": 3,
    "army-camp": 3, "laboratory": 3, "spell-factory": 3, "dark-spell-factory": 3,
}

TH_PATTERN = re.compile(r"^th\d+$")
_BASE_DIR_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
_QUAD_RE = re.compile(
    r"quad\s*(?:[（(][^）)]*[）)])?\s*=\s*"
    r"(\[\s*\[[^\]]*\]\s*(?:,\s*\[[^\]]*\]\s*){3}\])"
)


def type_cn(t: str) -> str:
    return TYPE_CN.get(t, t)


def type_size(t: str) -> int:
    return TYPE_SIZE.get(t, TYPE_SIZE_DEFAULT)


# ---------------------------------------------------------------------------
# quad 解析 / 菱形排序
# ---------------------------------------------------------------------------

def parse_quad(note):
    """从 layout.json 的 note 文本里解析 quad=[[x,y]...]（上,右,下,左，base.png 像素）。

    兼容 6 个生产阵的写法：
      - "quad=[[1180,90],...]"
      - "quad(上,右,下,左)=[[500,12],...]"
      - "quad=[[...]]（RANSAC ...）"
    解析不了返回 None（不抛异常）。
    """
    if not isinstance(note, str) or not note:
        return None
    m = _QUAD_RE.search(note)
    if not m:
        return None
    try:
        raw = json.loads(m.group(1))
    except (ValueError, TypeError):
        return None
    if not isinstance(raw, list) or len(raw) != 4:
        return None
    quad = []
    for pt in raw:
        if not isinstance(pt, (list, tuple)) or len(pt) != 2:
            return None
        vals = []
        for v in pt:
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                return None
            v = float(v)
            if not math.isfinite(v):
                return None
            vals.append(v)
        quad.append(vals)
    return quad


def order_diamond(quad):
    """四点整理成 上、右、下、左 顺序（与 clashlab.geo.order_diamond 同语义）。"""
    if not isinstance(quad, (list, tuple)) or len(quad) != 4:
        raise ValueError("quad 需要四个点")
    pts = []
    for pt in quad:
        if not isinstance(pt, (list, tuple)) or len(pt) != 2:
            raise ValueError("quad 每个点必须是 [x, y]")
        x, y = float(pt[0]), float(pt[1])
        if not (math.isfinite(x) and math.isfinite(y)):
            raise ValueError("quad 含非有限数值")
        pts.append([x, y])
    cx = sum(p[0] for p in pts) / 4.0
    cy = sum(p[1] for p in pts) / 4.0
    pts.sort(key=lambda p: math.atan2(p[1] - cy, p[0] - cx))
    top = min(range(4), key=lambda i: (pts[i][1], pts[i][0]))
    pts = pts[top:] + pts[:top]
    if pts[1][0] < pts[0][0]:            # 第二点应在右侧
        pts = [pts[0], pts[3], pts[2], pts[1]]
    return pts


def _polygon_area(quad):
    area = 0.0
    for i in range(4):
        x0, y0 = quad[i]
        x1, y1 = quad[(i + 1) % 4]
        area += x0 * y1 - x1 * y0
    return abs(area) / 2.0


# ---------------------------------------------------------------------------
# 单应矩阵：tile(grid 坐标) -> base.png 像素
# ---------------------------------------------------------------------------

def _solve_linear(a, b):
    """高斯消元（部分选主元）解 a·x=b；退化抛 ValueError。"""
    n = len(b)
    m = [list(row) + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[piv][col]) < 1e-12:
            raise ValueError("线性方程组退化（四点在一条线上？）")
        if piv != col:
            m[col], m[piv] = m[piv], m[col]
        pv = m[col][col]
        for r in range(col + 1, n):
            f = m[r][col] / pv
            if f:
                for c in range(col, n + 1):
                    m[r][c] -= f * m[col][c]
    x = [0.0] * n
    for r in range(n - 1, -1, -1):
        s = m[r][n] - sum(m[r][c] * x[c] for c in range(r + 1, n))
        x[r] = s / m[r][r]
    return x


def homography_from_quad(quad, grid=GRID_DEFAULT):
    """四点（上,右,下,左，任意顺序）→ 3x3 单应（tile 坐标 -> 像素）。"""
    grid = int(grid)
    if grid <= 0:
        raise ValueError("grid 必须为正整数")
    q = order_diamond(quad)
    if _polygon_area(q) < 1e-6:
        raise ValueError("quad 退化（面积≈0）")
    src = [(0.0, 0.0), (float(grid), 0.0), (float(grid), float(grid)), (0.0, float(grid))]
    a, b = [], []
    for (u, v), (x, y) in zip(src, q):
        a.append([u, v, 1.0, 0.0, 0.0, 0.0, -x * u, -x * v])
        b.append(x)
        a.append([0.0, 0.0, 0.0, u, v, 1.0, -y * u, -y * v])
        b.append(y)
    h = _solve_linear(a, b)
    return [[h[0], h[1], h[2]], [h[3], h[4], h[5]], [h[6], h[7], 1.0]]


def invert3x3(m):
    """3x3 求逆（伴随矩阵 / 行列式），不可逆抛 ValueError。"""
    a, b, c = m[0]
    d, e, f = m[1]
    g, h, i = m[2]
    det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    if abs(det) < 1e-12:
        raise ValueError("矩阵不可逆")
    return [
        [(e * i - f * h) / det, (c * h - b * i) / det, (b * f - c * e) / det],
        [(f * g - d * i) / det, (a * i - c * g) / det, (c * d - a * f) / det],
        [(d * h - e * g) / det, (b * g - a * h) / det, (a * e - b * d) / det],
    ]


def apply_h(h, x, y):
    """3x3 单应作用于点；齐次项退化为 0 时返回 None。"""
    w = h[2][0] * x + h[2][1] * y + h[2][2]
    if abs(w) < 1e-12:
        return None
    return ((h[0][0] * x + h[0][1] * y + h[0][2]) / w,
            (h[1][0] * x + h[1][1] * y + h[1][2]) / w)


def tile_to_px(h, gx, gy):
    """tile 坐标（可为小数，如单元中心 8.5,2.5）→ base.png 像素。"""
    pt = apply_h(h, float(gx), float(gy))
    if pt is None:
        raise ValueError("单应映射退化")
    return pt


def cell_to_px(h, tx, ty):
    """整数 tile（单元格索引）→ 该单元格几何中心的像素。"""
    return tile_to_px(h, int(tx) + 0.5, int(ty) + 0.5)


def px_to_tile(hn, x, y):
    """像素 → tile 坐标（连续值，未取整）。"""
    pt = apply_h(hn, float(x), float(y))
    if pt is None:
        raise ValueError("单应逆映射退化")
    return pt


def px_to_cell(hn, x, y, grid=GRID_DEFAULT, clamp=True):
    """像素 → 整数单元格索引 (col, row)。

    floor 语义（整数 tile = 单元格索引，中心在 +0.5）；
    clamp=True 时把域外点击夹到 0..grid-1，clamp=False 时域外返回 None。
    """
    pt = apply_h(hn, float(x), float(y))
    if pt is None:
        return None
    gx, gy = math.floor(pt[0]), math.floor(pt[1])
    if 0 <= gx < grid and 0 <= gy < grid:
        return int(gx), int(gy)
    if not clamp:
        return None
    return (min(max(int(gx), 0), grid - 1), min(max(int(gy), 0), grid - 1))


def geometry_for_layout(layout_doc, override_quad=None):
    """layout + 可选 override quad → {grid, quad, H, Hinv, quad_source}。

    override（用户在「校准网格」里拖出来的 4 角）优先于 layout.json note 里的 quad；
    没有 override 或 override 非法时回落到 layout.json。
    """
    if not isinstance(layout_doc, dict):
        return None
    grid = layout_doc.get("grid", GRID_DEFAULT)
    if isinstance(grid, bool) or not isinstance(grid, int) or grid <= 0:
        grid = GRID_DEFAULT
    quad, source = effective_quad(layout_doc, override_quad)
    if quad is None:
        return None
    h = homography_from_quad(quad, grid)
    return {"grid": grid, "quad": order_diamond(quad), "H": h, "Hinv": invert3x3(h),
            "quad_source": source}


# ---------------------------------------------------------------------------
# 网格校准（quad override）：out/annotate/NN_quad.json 优先于 layout.json
# ---------------------------------------------------------------------------

OVERRIDE_QUAD_SUFFIX = "_quad.json"


def validate_quad(quad, image_size=None):
    """校验像素 quad：4 个有限数值点、非退化、面积不过小；给定图像尺寸时限制在图像内（10% 容差）。"""
    errors = []
    if not isinstance(quad, (list, tuple)) or len(quad) != 4:
        return ["quad 必须是 4 个 [x, y] 点"]
    pts = []
    for i, pt in enumerate(quad):
        if not isinstance(pt, (list, tuple)) or len(pt) != 2:
            errors.append("quad[%d] 必须是 [x, y]" % i)
            continue
        vals = []
        ok = True
        for v in pt:
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(float(v)):
                errors.append("quad[%d] 含非数值/非有限值：%r" % (i, v))
                ok = False
                break
            vals.append(float(v))
        if ok:
            pts.append(vals)
    if errors:
        return errors
    try:
        q = order_diamond(pts)
    except ValueError as exc:
        return ["quad 无法排序：" + str(exc)]
    if _polygon_area(q) < 100.0:
        errors.append("quad 退化（面积 < 100 平方像素，四点可能共线/重合）")
    if isinstance(image_size, (list, tuple)) and len(image_size) == 2:
        try:
            w, h = float(image_size[0]), float(image_size[1])
        except (TypeError, ValueError):
            w = h = 0.0
        if w > 0 and h > 0:
            # 允许角点落在截图之外：导入的截图常没截全整张地图，角点本来就可能出界。
            # 只拦「明显误拖」（超出 1 张图尺寸）与退化情形。
            pad_x, pad_y = w, h
            for i, (x, y) in enumerate(q):
                if not (-pad_x <= x <= w + pad_x and -pad_y <= y <= h + pad_y):
                    errors.append("quad[%d]=(%g,%g) 离 base.png 太远（超过 1 张图尺寸），疑似误拖"
                                  % (i, x, y))
    return errors


def normalize_quad(quad):
    """校验并整理成「上、右、下、左」顺序；非法抛 ValueError。"""
    errors = validate_quad(quad)
    if errors:
        raise ValueError("quad 非法：" + "；".join(errors))
    return order_diamond(quad)


def geometry_for_quad(quad, grid=GRID_DEFAULT):
    """直接用一组已校准 quad 求 H/Hinv（前端校准预览 / 测试用）。"""
    q = normalize_quad(quad)
    h = homography_from_quad(q, grid)
    return {"grid": int(grid), "quad": q, "H": h, "Hinv": invert3x3(h), "quad_source": "override"}


def effective_quad(layout_doc, override_quad=None):
    """返回 (quad, source)：override 合法则优先，否则回落 layout.json note，都没有则 (None, "none")。"""
    layout_quad = None
    if isinstance(layout_doc, dict):
        layout_quad = parse_quad(layout_doc.get("note") or "")
    if override_quad is not None and not validate_quad(override_quad):
        return order_diamond(override_quad), "override"
    if layout_quad is not None:
        return layout_quad, "layout"
    return None, "none"


def override_quad_rel_path(base_id):
    return os.path.join(OUT_DIR_REL, "%s%s" % (str(base_id), OVERRIDE_QUAD_SUFFIX))


def override_quad_path(root, base_id):
    return os.path.join(root, override_quad_rel_path(base_id))


def load_override_quad(root, base_id):
    """读 out/annotate/<id>_quad.json；缺失/损坏/非法均返回 None（回落到 layout）。"""
    data = load_json(override_quad_path(root, base_id))
    if not isinstance(data, dict):
        return None
    quad = data.get("quad")
    if validate_quad(quad):
        return None
    return order_diamond(quad)


def save_override_quad(root, base_id, quad, image_size=None):
    """保存校准 quad（原子写）；非法 quad 抛 ValueError（服务端返回 400）。"""
    errors = validate_quad(quad, image_size=image_size)
    if errors:
        raise ValueError("quad 非法：" + "；".join(errors))
    q = order_diamond(quad)
    doc = {
        "quad": q,
        "saved_at": now_iso(),
        "note": "tools/annotate 网格校准覆盖：优先于 layout.json 的 quad（DELETE /api/quad 可重置）",
    }
    path = override_quad_path(root, base_id)
    write_json_atomic(path, doc)
    return {"quad": q, "path": path, "saved_at": doc["saved_at"]}


def delete_override_quad(root, base_id):
    """删除校准覆盖；返回是否真的删掉了文件。"""
    path = override_quad_path(root, base_id)
    try:
        os.remove(path)
        return True
    except FileNotFoundError:
        return False
    except OSError:
        return False


# ---------------------------------------------------------------------------
# schema 校验 / 规范化
# ---------------------------------------------------------------------------

def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(float(v))


def validate_layout(doc, grid=None):
    """校验 layout（annotated 与 bases/*/layout.json 同 schema），返回错误列表（空=合法）。"""
    errors = []
    if not isinstance(doc, dict):
        return ["layout 根节点必须是 JSON 对象"]

    name = doc.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append("name 必须是非空字符串")

    g = doc.get("grid")
    g_eff = GRID_DEFAULT
    if isinstance(g, bool) or not _is_int(g) or not (20 <= g <= 64):
        errors.append("grid 必须是 20..64 的整数")
        if _is_int(grid):
            g_eff = int(grid)
    else:
        g_eff = g
        if _is_int(grid) and g != grid:
            errors.append("grid=%s 与预期 %s 不一致" % (g, grid))

    note = doc.get("note", "")
    if not isinstance(note, str):
        errors.append("note 必须是字符串")

    buildings = doc.get("buildings")
    if not isinstance(buildings, list):
        errors.append("buildings 必须是数组")
    else:
        for i, b in enumerate(buildings):
            pre = "buildings[%d]" % i
            if not isinstance(b, dict):
                errors.append(pre + " 必须是对象")
                continue
            t = b.get("type")
            if not isinstance(t, str) or t not in ALLOWED_TYPES:
                errors.append("%s.type 非法：%r（必须是调色板里的类型）" % (pre, t))
            tile = b.get("tile")
            if not (isinstance(tile, (list, tuple)) and len(tile) == 2):
                errors.append(pre + ".tile 必须是 [x, y]")
            else:
                ok = True
                for j, v in enumerate(tile):
                    if not _is_int(v):
                        errors.append("%s.tile[%d] 必须是整数，得到 %r" % (pre, j, v))
                        ok = False
                        break
                # 允许贴到 grid 边界：生产 layout 里确有 tile=44 的夹边条目（01 阵两栋），
                # 不能因为「预填原样保存」而报错；网页点选永远只会产生 0..grid-1。
                if ok and not (0 <= tile[0] <= g_eff and 0 <= tile[1] <= g_eff):
                    errors.append("%s.tile 越界：%s（允许 0..%d）" % (pre, list(tile), g_eff))
            src = b.get("source")
            if src is not None and (not isinstance(src, str) or not src.strip()):
                errors.append(pre + ".source 必须是非空字符串")
            conf = b.get("conf")
            if conf is not None:
                if not _is_num(conf) or not (0.0 <= float(conf) <= 1.0):
                    errors.append(pre + ".conf 必须是 0..1 的数字")
            bn = b.get("note")
            if bn is not None and not isinstance(bn, str):
                errors.append(pre + ".note 必须是字符串")

    walls = doc.get("walls", [])
    if walls is None:
        walls = []
    if not isinstance(walls, list):
        errors.append("walls 必须是数组")
    else:
        for i, p in enumerate(walls):
            if not (isinstance(p, (list, tuple)) and len(p) == 2 and _is_int(p[0]) and _is_int(p[1])):
                errors.append("walls[%d] 必须是 [int, int]" % i)
                continue
            # 墙点允许贴坐标边界 grid（生产数据里就有 [0,44]）
            if not (0 <= p[0] <= g_eff and 0 <= p[1] <= g_eff):
                errors.append("walls[%d] 越界：%s（允许 0..%d）" % (i, list(p), g_eff))
    return errors


def normalize_layout(doc, grid=None):
    """规范化成与生产 layout.json 完全同构的对象（键顺序固定，未知键丢弃）。"""
    if not isinstance(doc, dict):
        raise ValueError("layout 必须是 JSON 对象")
    g = grid
    if not _is_int(g):
        g = doc.get("grid", GRID_DEFAULT)
    if isinstance(g, bool) or not _is_int(g) or g <= 0:
        g = GRID_DEFAULT
    note = doc.get("note")
    if not isinstance(note, str):
        note = ""
    buildings = []
    raw_buildings = doc.get("buildings")
    if isinstance(raw_buildings, list):
        for b in raw_buildings:
            if not isinstance(b, dict):
                continue
            tile = b.get("tile")
            try:
                tx, ty = int(tile[0]), int(tile[1])
            except (TypeError, ValueError, IndexError, KeyError):
                tx, ty = 0, 0
            conf = b.get("conf", 1.0)
            try:
                conf = float(conf)
            except (TypeError, ValueError):
                conf = 1.0
            conf = min(max(conf, 0.0), 1.0)
            item = {
                "type": str(b.get("type") or ""),
                "tile": [tx, ty],
                "source": str(b.get("source") or "manual"),
                "conf": conf,
                "note": str(b.get("note") or ""),
            }
            # 等级（可选）：标注工具里填的整数，1..99；其它值丢弃
            lv = b.get("level")
            if isinstance(lv, int) and not isinstance(lv, bool) and 1 <= lv <= 99:
                item["level"] = int(lv)
            buildings.append(item)
    walls = []
    raw_walls = doc.get("walls")
    if isinstance(raw_walls, list):
        for p in raw_walls:
            try:
                walls.append([int(p[0]), int(p[1])])
            except (TypeError, ValueError, IndexError):
                continue
    return {
        "name": str(doc.get("name") or ""),
        "grid": int(g),
        "note": note,
        "buildings": buildings,
        "walls": walls,
    }


# ---------------------------------------------------------------------------
# 预填合并 / 人工修改差异
# ---------------------------------------------------------------------------

def resolve_prefill(layout_doc, annotated_doc=None):
    """决定预填来源：已标注文件合法则续编辑（annotated），否则用 layout。"""
    base = normalize_layout(layout_doc) if isinstance(layout_doc, dict) else None
    if base is None:
        raise ValueError("layout 不可用")
    if isinstance(annotated_doc, dict) and not validate_layout(annotated_doc):
        return normalize_layout(annotated_doc), "annotated"
    return base, "layout"


def _bkey(b):
    try:
        return (str(b.get("type") or ""), int(b["tile"][0]), int(b["tile"][1]))
    except (TypeError, ValueError, IndexError, KeyError):
        return (str(b.get("type") or ""), -1, -1)


def diff_layout(before, after):
    """人工修改统计：exact → retyped → moved → added/removed（贪心匹配，确定性）。"""
    b_list = [b for b in (before.get("buildings") if isinstance(before, dict) else []) or [] if isinstance(b, dict)]
    a_list = [b for b in (after.get("buildings") if isinstance(after, dict) else []) or [] if isinstance(b, dict)]
    b_used = [False] * len(b_list)
    a_used = [False] * len(a_list)
    unchanged = retyped = moved = 0

    # 1) type + tile 完全一致
    by_key = {}
    for ai, a in enumerate(a_list):
        by_key.setdefault(_bkey(a), []).append(ai)
    for bi, b in enumerate(b_list):
        bucket = by_key.get(_bkey(b))
        if bucket:
            ai = bucket.pop(0)
            b_used[bi] = True
            a_used[ai] = True
            unchanged += 1

    # 2) tile 相同、类型不同 → 判型修正
    by_tile = {}
    for ai, a in enumerate(a_list):
        if not a_used[ai]:
            k = (int(a["tile"][0]), int(a["tile"][1]))
            by_tile.setdefault(k, []).append(ai)
    for bi, b in enumerate(b_list):
        if b_used[bi]:
            continue
        k = (int(b["tile"][0]), int(b["tile"][1]))
        bucket = by_tile.get(k)
        if bucket:
            ai = bucket.pop(0)
            b_used[bi] = True
            a_used[ai] = True
            retyped += 1

    # 3) 类型相同、tile 不同 → 拖动修正（取最近位置配对）
    by_type = {}
    for ai, a in enumerate(a_list):
        if not a_used[ai]:
            by_type.setdefault(str(a.get("type") or ""), []).append(ai)
    for bi, b in enumerate(b_list):
        if b_used[bi]:
            continue
        bucket = by_type.get(str(b.get("type") or ""))
        if bucket:
            bx, by_ = int(b["tile"][0]), int(b["tile"][1])

            def _dist(ai):
                a = a_list[ai]
                return abs(int(a["tile"][0]) - bx) + abs(int(a["tile"][1]) - by_)

            ai = min(bucket, key=_dist)
            bucket.remove(ai)
            b_used[bi] = True
            a_used[ai] = True
            moved += 1

    removed = sum(1 for u in b_used if not u)
    added = sum(1 for u in a_used if not u)
    return {
        "added": added, "removed": removed, "moved": moved, "retyped": retyped,
        "unchanged": unchanged, "edits": added + removed + moved + retyped,
    }


# ---------------------------------------------------------------------------
# 时间 / 摘要
# ---------------------------------------------------------------------------

_PROV_MARKER = "tools/annotate 人工校正"


def with_provenance(note, edits, candidate="layout", stamp=None, quad_source=None):
    """把「人工校正」溯源写进 note（重复保存只保留最新一条，不叠加）。

    备注里本身可能带分号（provenance 自己的括号里就有），所以不用正则啃后缀：
    从最后一个「；<marker>」处截断，再补新的。
    """
    stamp = stamp or now_iso()
    text = note or ""
    cut = -1
    for sep in ("；" + _PROV_MARKER, ";" + _PROV_MARKER):
        pos = text.rfind(sep)
        if pos > cut:
            cut = pos
    base = (text[:cut] if cut >= 0 else text).rstrip()
    extra = "" if (not quad_source or quad_source == "layout") else "；quad=" + str(quad_source)
    prov = "tools/annotate 人工校正 %s（edits=%d；candidate=%s%s）" % (
        stamp, int(edits or 0), candidate or "layout", extra)
    return (base + "；" + prov) if base else prov


def now_iso():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def _mtime_iso(path):
    try:
        return datetime.datetime.fromtimestamp(os.path.getmtime(path)).astimezone().isoformat(timespec="seconds")
    except OSError:
        return ""


def _th_num(th):
    m = re.search(r"(\d+)", str(th or ""))
    return int(m.group(1)) if m else 0


def make_summary_entry(base_id, th, doc, diff, elapsed_ms, status="done", candidate="layout", name=None, now=None):
    """单阵 summary 条目（写入 out/annotate/summary.json）。"""
    doc_n = normalize_layout(doc)
    diff = diff or {}
    return {
        "th": str(th),
        "base": str(base_id),
        "name": str(name if name is not None else doc_n["name"]),
        "candidate": str(candidate or "layout"),
        "buildings": len(doc_n["buildings"]),
        "walls": len(doc_n["walls"]),
        "manual_edits": int(diff.get("edits", 0) or 0),
        "unchanged": int(diff.get("unchanged", 0) or 0),
        "added": int(diff.get("added", 0) or 0),
        "removed": int(diff.get("removed", 0) or 0),
        "moved": int(diff.get("moved", 0) or 0),
        "retyped": int(diff.get("retyped", 0) or 0),
        "elapsed_ms": int(max(0, int(elapsed_ms or 0))),
        "status": status if status in ("done", "skipped", "in_progress") else "done",
        "updated_at": now or now_iso(),
    }


def build_summary(entries):
    """聚合 summary（按 TH 数字、阵号排序；totals 由条目重算）。"""
    bases = []
    for e in entries or []:
        if not isinstance(e, dict):
            continue
        item = dict(e)
        item["th"] = str(item.get("th") or "")
        item["base"] = str(item.get("base") or "")
        bases.append(item)
    bases.sort(key=lambda e: (_th_num(e.get("th")), str(e.get("base"))))
    totals = {
        "bases": len(bases),
        "done": sum(1 for e in bases if e.get("status") == "done"),
        "skipped": sum(1 for e in bases if e.get("status") == "skipped"),
        "buildings": sum(int(e.get("buildings", 0) or 0) for e in bases),
        "manual_edits": sum(int(e.get("manual_edits", 0) or 0) for e in bases),
        "elapsed_ms": sum(int(e.get("elapsed_ms", 0) or 0) for e in bases),
    }
    return {
        "schema": ANNOTATE_SCHEMA,
        "tool": SUMMARY_TOOL,
        "generated_at": now_iso(),
        "totals": totals,
        "bases": bases,
    }


def upsert_summary(summary, entry):
    """把一条 base 条目写入 summary（同 th+base 覆盖，其余保留）。"""
    data = summary if isinstance(summary, dict) else {}
    kept = [dict(b) for b in (data.get("bases") or []) if isinstance(b, dict)
            and not (str(b.get("th")) == str(entry.get("th")) and str(b.get("base")) == str(entry.get("base")))]
    kept.append(dict(entry))
    return build_summary(kept)


def empty_summary():
    return build_summary([])


# ---------------------------------------------------------------------------
# 读写
# ---------------------------------------------------------------------------

def load_json(path):
    """读 JSON；文件不存在 / 内容非法返回 None（调用方决定回退）。"""
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except (OSError, ValueError, UnicodeError):
        return None


def write_json_atomic(path, obj, indent=2):
    """原子写 JSON：同目录 .tmp → flush+fsync → os.replace（沿用项目原子写约定）。"""
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    text = json.dumps(obj, ensure_ascii=False, indent=indent) + "\n"
    fd, tmp = tempfile.mkstemp(prefix=".tmp.", suffix=".json", dir=parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return path


def load_summary(path):
    """读 summary；缺失/非法时返回空 summary（不抛异常）。"""
    data = load_json(path)
    if isinstance(data, dict) and isinstance(data.get("bases"), list):
        return build_summary([b for b in data["bases"] if isinstance(b, dict)])
    return build_summary([])


# ---------------------------------------------------------------------------
# 路径 / 发现
# ---------------------------------------------------------------------------

def annotated_rel_path(base_id):
    return os.path.join(OUT_DIR_REL, "%s_annotated.json" % str(base_id))


def annotated_path(root, base_id):
    return os.path.join(root, annotated_rel_path(base_id))


def summary_rel_path():
    return os.path.join(OUT_DIR_REL, SUMMARY_NAME)


def summary_path(root):
    return os.path.join(root, summary_rel_path())


def _candidate_title(path, fallback):
    doc = load_json(path)
    if isinstance(doc, dict) and isinstance(doc.get("name"), str) and doc["name"].strip():
        return doc["name"].strip()
    return fallback


def _discover_candidates(base_dir):
    """候选方案：<base>/layouts/*.json 以及 <base>/layout*.json（layout.json 除外）。"""
    cands = []
    seen = {"layout"}
    layouts_dir = os.path.join(base_dir, "layouts")
    if os.path.isdir(layouts_dir):
        for fn in sorted(os.listdir(layouts_dir)):
            if not fn.lower().endswith(".json"):
                continue
            path = os.path.join(layouts_dir, fn)
            if not os.path.isfile(path):
                continue
            cid = os.path.splitext(fn)[0]
            if cid in seen:
                continue
            seen.add(cid)
            cands.append({"id": cid, "path": path, "source": "layouts/" + fn,
                          "title": _candidate_title(path, cid)})
    for fn in sorted(os.listdir(base_dir)):
        low = fn.lower()
        if not low.endswith(".json") or fn == "layout.json" or not low.startswith("layout"):
            continue
        path = os.path.join(base_dir, fn)
        if not os.path.isfile(path):
            continue
        cid = os.path.splitext(fn)[0]
        if cid in seen:
            continue
        seen.add(cid)
        cands.append({"id": cid, "path": path, "source": fn, "title": _candidate_title(path, cid)})
    return cands


def discover_bases(root, th="th16"):
    """发现 bases/<th>/NN（要求 base.png + layout.json 同时存在），含候选方案与已标注状态。"""
    th_dir = os.path.join(root, "bases", str(th))
    result = []
    if not os.path.isdir(th_dir):
        return result
    for name in sorted(os.listdir(th_dir)):
        if not _BASE_DIR_PATTERN.match(name):
            continue
        base_dir = os.path.join(th_dir, name)
        if not os.path.isdir(base_dir):
            continue
        image = os.path.join(base_dir, "base.png")
        layout = os.path.join(base_dir, "layout.json")
        if not (os.path.isfile(image) and os.path.isfile(layout)):
            continue
        doc = load_json(layout)
        if not isinstance(doc, dict):
            continue
        ann_path = annotated_path(root, name)
        ann_doc = load_json(ann_path)
        if isinstance(ann_doc, dict):
            annotated = {
                "exists": True, "path": ann_path,
                "buildings": len(ann_doc.get("buildings") or []),
                "updated_at": _mtime_iso(ann_path),
            }
        else:
            annotated = {"exists": False, "path": ann_path, "buildings": 0, "updated_at": ""}
        result.append({
            "th": str(th),
            "id": name,
            "label": "阵 " + name,
            "dir": base_dir,
            "image": image,
            "layout": layout,
            "layout_name": str(doc.get("name") or ""),
            "grid": int(doc.get("grid") or GRID_DEFAULT),
            "has_quad": parse_quad(doc.get("note") or "") is not None,
            "prefilled": len(doc.get("buildings") or []),
            "candidates": _discover_candidates(base_dir),
            "annotated": annotated,
        })
    return result


def discover_groups(root):
    """扫描 bases/<thN>/ 分组（数字排序），每组返回 bases 列表。"""
    bases_dir = os.path.join(root, "bases")
    groups = []
    if not os.path.isdir(bases_dir):
        return groups
    for name in sorted(os.listdir(bases_dir)):
        if not TH_PATTERN.match(name):
            continue
        path = os.path.join(bases_dir, name)
        if not os.path.isdir(path):
            continue
        bases = discover_bases(root, name)
        if bases:
            groups.append({"th": name, "label": name.upper(), "bases": bases})
    groups.sort(key=lambda g: _th_num(g["th"]))
    return groups


# ---------------------------------------------------------------------------
# 图片尺寸（纯标准库：PNG / JPEG）
# ---------------------------------------------------------------------------

_PNG_SIG = b"\x89PNG\r\n\x1a\n"
_JPEG_SOF = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}


def image_size(path):
    """读 PNG/JPEG 宽高（只读文件头，不依赖 Pillow）；不认识返回 None。"""
    try:
        with open(path, "rb") as f:
            head = f.read(32)
    except OSError:
        return None
    if head.startswith(_PNG_SIG) and len(head) >= 24:
        w, h = struct.unpack(">II", head[16:24])
        return (int(w), int(h)) if w > 0 and h > 0 else None
    if head[:2] == b"\xff\xd8":
        try:
            with open(path, "rb") as f:
                data = f.read()
        except OSError:
            return None
        i, n = 2, len(data)
        while i + 9 < n:
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7 or marker == 0x01:
                i += 2
                continue
            seg_len = struct.unpack(">H", data[i + 2:i + 4])[0]
            if marker in _JPEG_SOF:
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                return (int(w), int(h)) if w > 0 and h > 0 else None
            i += 2 + seg_len
        return None
    return None
