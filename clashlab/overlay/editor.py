# -*- coding: utf-8 -*-
"""确认编辑器纯逻辑：命中测试、候选增删改、拖动/缩放、冻结产物生成。

铁律：
  * 本模块不 import ImGui、不建窗、不读屏；全部是纯函数与内存模型；
  * 渲染坐标（render px）= 原始截图/overlay.png 的 1280x720 像素空间；
  * 面板坐标 -> 图片坐标 -> 渲染坐标 的两级反算只走本模块 ViewTransform；
  * 瓦片换算只走 clashlab.geo.Calib.tile_to_px / px_to_tile，不写第二套公式；
  * 冻结动作幂等：同输入重复冻结，current.json 字节一致，快照不产生重复副本。

坐标空间约定：
  panel px   ImGui 面板本地像素（窗口内）
  image px   底图像素（整帧源时 == render px）
  render px  1280x720 渲染坐标系（候选 bbox、quad 都在这个空间）
"""
import hashlib
import json
import os
import tempfile
import time
from dataclasses import dataclass, field

try:
    from ..geo import Calib
except ImportError:  # pragma: no cover（脚本直跑兜底）
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from clashlab.geo import Calib


# ================================================================ 面板显示变换

@dataclass
class ViewTransform:
    """底图在面板可用区内等比缩放（contain，居中留白），两级反算。

    构造：img_w/img_h 底图像素尺寸；avail=(ax, ay, aw, ah) 面板可用区；
    src_offset=(x0, y0) 当底图是源截图裁剪时，image->render 的平移（整帧传 0,0）；
    render_w/render_h 渲染坐标系尺寸（默认 1280x720），底图非整帧时按比例换算。
    """
    img_w: float
    img_h: float
    ax: float = 0.0
    ay: float = 0.0
    aw: float = 1.0
    ah: float = 1.0
    src_x0: float = 0.0
    src_y0: float = 0.0
    render_w: float = 1280.0
    render_h: float = 720.0
    scale: float = 1.0
    off_x: float = 0.0
    off_y: float = 0.0
    disp_w: float = 0.0
    disp_h: float = 0.0

    def __post_init__(self):
        self.fit()

    def fit(self):
        if self.img_w > 0 and self.img_h > 0 and self.aw > 0 and self.ah > 0:
            self.scale = min(self.aw / self.img_w, self.ah / self.img_h)
        else:
            self.scale = 1.0
        self.disp_w = self.img_w * self.scale
        self.disp_h = self.img_h * self.scale
        self.off_x = self.ax + (self.aw - self.disp_w) / 2.0
        self.off_y = self.ay + (self.ah - self.disp_h) / 2.0

    # panel -> image -> render
    def panel_to_image(self, px, py):
        return ((px - self.off_x) / self.scale, (py - self.off_y) / self.scale)

    def image_to_panel(self, ix, iy):
        return (self.off_x + ix * self.scale, self.off_y + iy * self.scale)

    def image_to_render(self, ix, iy):
        sx = self.render_w / self.img_w if self.img_w else 1.0
        sy = self.render_h / self.img_h if self.img_h else 1.0
        return (ix * sx + self.src_x0, iy * sy + self.src_y0)

    def render_to_image(self, rx, ry):
        sx = self.render_w / self.img_w if self.img_w else 1.0
        sy = self.render_h / self.img_h if self.img_h else 1.0
        return ((rx - self.src_x0) / sx, (ry - self.src_y0) / sy)

    def panel_to_render(self, px, py):
        ix, iy = self.panel_to_image(px, py)
        return self.image_to_render(ix, iy)

    def render_to_panel(self, rx, ry):
        ix, iy = self.render_to_image(rx, ry)
        return self.image_to_panel(ix, iy)


# ================================================================ 矩形

@dataclass
class Rect:
    x0: float
    y0: float
    x1: float
    y1: float

    def normalized(self):
        if self.x1 < self.x0:
            self.x0, self.x1 = self.x1, self.x0
        if self.y1 < self.y0:
            self.y0, self.y1 = self.y1, self.y0
        return self

    @property
    def w(self):
        return max(0.0, self.x1 - self.x0)

    @property
    def h(self):
        return max(0.0, self.y1 - self.y0)

    @property
    def center(self):
        return ((self.x0 + self.x1) / 2.0, (self.y0 + self.y1) / 2.0)

    def contains(self, px, py, pad=0.0):
        return (self.x0 - pad <= px <= self.x1 + pad
                and self.y0 - pad <= py <= self.y1 + pad)

    def corners(self):
        return {
            "nw": (self.x0, self.y0),
            "ne": (self.x1, self.y0),
            "sw": (self.x0, self.y1),
            "se": (self.x1, self.y1),
        }

    def corner_at(self, px, py, grab=10.0):
        """命中哪个拖角（优先角区），未中返回 None。grab 为面板像素半径，
        调用方需按 scale 换算成渲染像素后传入。"""
        for name, (cx, cy) in self.corners().items():
            if abs(px - cx) <= grab and abs(py - cy) <= grab:
                return name
        return None

    def moved(self, dx, dy):
        return Rect(self.x0 + dx, self.y0 + dy, self.x1 + dx, self.y1 + dy)

    def resized(self, corner, dx, dy, min_size=6.0):
        """按拖角拉伸；角名 nw/ne/sw/se。返回新 Rect，保证 min_size。"""
        x0, y0, x1, y1 = self.x0, self.y0, self.x1, self.y1
        if corner in ("nw", "sw"):
            x0 += dx
        else:
            x1 += dx
        if corner in ("nw", "ne"):
            y0 += dy
        else:
            y1 += dy
        r = Rect(x0, y0, x1, y1).normalized()
        if r.w < min_size:
            if corner in ("nw", "sw"):
                r.x0 = r.x1 - min_size
            else:
                r.x1 = r.x0 + min_size
        if r.h < min_size:
            if corner in ("nw", "ne"):
                r.y0 = r.y1 - min_size
            else:
                r.y1 = r.y0 + min_size
        return r

    def to_list(self):
        return [self.x0, self.y0, self.x1, self.y1]

    @classmethod
    def from_list(cls, bbox):
        x0, y0, x1, y1 = [float(v) for v in bbox]
        return cls(x0, y0, x1, y1).normalized()


# ================================================================ 候选模型

CORNERS = ("nw", "ne", "sw", "se")


class EditorModel:
    """候选集内存模型（渲染坐标空间）。

    candidates 项字段：id/label/type/bbox=[x0,y0,x1,y1]/confidence/tile/
    hidden/selected/manual/edit。edit ∈ kept|moved|resized|added。
    """

    def __init__(self, candidates=None, calib=None):
        self.candidates = []
        self.calib = calib
        self._seq = 0
        for c in candidates or []:
            self.add(c.get("bbox"), c.get("label", "未命名"),
                     confidence=c.get("confidence", 0.0),
                     cid=c.get("id"), ctype=c.get("type"),
                     tile=c.get("tile"), keep_flag=True)

    # ---------- 增删改 ----------
    def add(self, bbox, label="未命名", confidence=0.0, cid=None,
            ctype=None, tile=None, keep_flag=False, edit="added"):
        rect = Rect.from_list(bbox).normalized()
        if cid is None:
            self._seq += 1
            cid = f"u{self._seq}"
        item = {
            "id": str(cid),
            "label": str(label or "未命名"),
            "type": ctype or str(label or "unknown"),
            "bbox": rect.to_list(),
            "confidence": float(confidence or 0.0),
            "tile": tile,
            "hidden": False,
            "selected": False,
            "manual": True,
            "edit": edit,
        }
        if keep_flag:  # 导入的识别候选不算人工修改
            item["manual"] = False
            item["edit"] = "kept"
        self.candidates.append(item)
        return item

    def delete(self, cid):
        before = len(self.candidates)
        self.candidates = [c for c in self.candidates if c["id"] != cid]
        return len(self.candidates) < before

    def delete_selected(self):
        return self.delete(self.selected_id())

    def get(self, cid):
        for c in self.candidates:
            if c["id"] == cid:
                return c
        return None

    def selected_id(self):
        for c in self.candidates:
            if c.get("selected"):
                return c["id"]
        return None

    def select(self, cid):
        for c in self.candidates:
            c["selected"] = c["id"] == cid

    def deselect(self):
        for c in self.candidates:
            c["selected"] = False

    def rename_selected(self, label):
        c = self.get(self.selected_id())
        if c:
            c["label"] = str(label or c["label"])
            c["manual"] = True
            if c["edit"] == "kept":
                c["edit"] = "moved"
            return True
        return False

    def toggle_hidden(self, cid):
        c = self.get(cid)
        if c:
            c["hidden"] = not c["hidden"]
            return True
        return False

    # ---------- 命中与拖拽（渲染坐标） ----------
    def hit_test(self, rx, ry, corner_grab=10.0):
        """返回 (cid, part)；part ∈ nw/ne/sw/se/body；未中 (None, None)。

        后画的（列表尾部）优先，隐藏候选跳过。角区先判，再判体内。
        """
        for c in reversed(self.candidates):
            if c.get("hidden"):
                continue
            r = Rect.from_list(c["bbox"])
            corner = r.corner_at(rx, ry, corner_grab)
            if corner:
                return c["id"], corner
            if r.contains(rx, ry, pad=2.0):
                return c["id"], "body"
        return None, None

    def begin_drag(self, rx, ry, corner_grab=10.0):
        cid, part = self.hit_test(rx, ry, corner_grab)
        if cid is None:
            return None
        c = self.get(cid)
        self.select(cid)
        self._drag = {"id": cid, "part": part, "start": Rect.from_list(c["bbox"]).to_list(),
                      "grab": (rx, ry)}
        return self._drag

    def drag_to(self, rx, ry):
        """当前拖拽点（渲染坐标）应用位移。返回是否成功。"""
        d = getattr(self, "_drag", None)
        if not d:
            return False
        c = self.get(d["id"])
        if c is None:
            self._drag = None
            return False
        ox, oy = d["grab"]
        dx, dy = rx - ox, ry - oy
        start = Rect.from_list(d["start"])
        if d["part"] == "body":
            new = start.moved(dx, dy)
            c["edit"] = "moved"
        else:
            new = start.resized(d["part"], dx, dy)
            c["edit"] = "resized"
        c["bbox"] = new.to_list()
        c["manual"] = True
        return True

    def end_drag(self):
        self._drag = None

    # ---------- 视图辅助 ----------
    def sorted_by_confidence(self):
        return sorted(self.candidates, key=lambda c: -c["confidence"])

    def visible(self):
        return [c for c in self.candidates if not c.get("hidden")]


# ================================================================ 冻结产物

LAYOUT_SCHEMA = 1
CURRENT_NAME = "layout_current.json"


def validate_layout_product(product):
    """校验冻结产物 schema，返回错误字符串列表（空列表=通过）。"""
    errors = []
    if not isinstance(product, dict):
        return ["product_not_dict"]
    for key in ("version", "grid", "source", "quad", "frozen_at", "buildings"):
        if key not in product:
            errors.append(f"missing_top_key:{key}")
    if not isinstance(product.get("buildings"), list):
        errors.append("buildings_not_list")
        return errors
    for i, b in enumerate(product["buildings"]):
        if not isinstance(b, dict):
            errors.append(f"building_{i}_not_dict")
            continue
        for key in ("id", "label", "bbox", "confidence", "manual"):
            if key not in b:
                errors.append(f"building_{i}_missing:{key}")
        bbox = b.get("bbox")
        if not (isinstance(bbox, list) and len(bbox) == 4):
            errors.append(f"building_{i}_bbox_bad")
        elif not all(isinstance(v, (int, float)) for v in bbox):
            errors.append(f"building_{i}_bbox_numeric")
        if not isinstance(b.get("manual"), bool):
            errors.append(f"building_{i}_manual_bool")
    return errors


def _tile_of(calib, bbox):
    """渲染坐标 bbox 中心 -> 瓦片格（Calib 唯一换算入口）；无 calib 返回 None。"""
    if calib is None:
        return None
    cx = (bbox[0] + bbox[2]) / 2.0
    cy = (bbox[1] + bbox[3]) / 2.0
    gx, gy = calib.px_to_tile(cx, cy)
    return [round(float(gx), 2), round(float(gy), 2)]


def freeze_layout(model, layouts_dir, source_meta=None, quad=None, grid=44,
                  current_name=CURRENT_NAME, clock=None):
    """冻结当前编辑态为 layout_<时间戳>.json，并刷新 layout_current.json。

    幂等：同模型同 meta 重复调用 -> current.json 字节一致；快照按内容哈希去重，
    不产生重复副本。返回 {ok, snapshot, current, message, product, errors}。
    """
    clock = clock or time.strftime
    frozen_at = clock("%Y-%m-%dT%H:%M:%S")
    source_meta = source_meta or {}
    manual_edits = sum(1 for c in model.candidates if c.get("manual"))

    buildings, removed = [], []
    for c in model.candidates:
        entry = {
            "id": c["id"],
            "type": c.get("type") or "unknown",
            "label": c["label"],
            "tile": _tile_of(model.calib, c["bbox"]),
            "bbox": [round(float(v), 2) for v in c["bbox"]],
            "confidence": round(float(c["confidence"]), 4),
            "manual": bool(c.get("manual")),
            "edit": c.get("edit", "kept"),
        }
        if c.get("hidden"):
            entry["edit"] = "deleted"
            removed.append({k: entry[k] for k in ("id", "label", "bbox", "edit")})
            continue
        buildings.append(entry)

    product = {
        "version": LAYOUT_SCHEMA,
        "schema": "overlay-layout@1",
        "name": f"layout_{clock('%Y%m%d_%H%M%S')}",
        "grid": int(grid),
        "note": "覆盖层 PANEL 确认编辑器冻结产物",
        "source": {
            "image": source_meta.get("image"),
            "candidates": source_meta.get("candidates"),
            "captured_at": source_meta.get("captured_at"),
            "tool": "overlay-panel-editor",
        },
        "quad": [[float(v) for v in pt] for pt in quad] if quad else None,
        "frozen_at": frozen_at,
        "editor": {"schema": LAYOUT_SCHEMA, "manual_edits": manual_edits,
                   "candidate_total": len(model.candidates)},
        "buildings": buildings,
        "removed": removed,
        "walls": [],
    }

    errors = validate_layout_product(product)
    if errors:
        return {"ok": False, "snapshot": None, "current": None,
                "message": "schema 校验失败：" + "; ".join(errors),
                "product": product, "errors": errors}

    os.makedirs(layouts_dir, exist_ok=True)
    payload = json.dumps(product, ensure_ascii=False, indent=2).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()[:12]

    # ---- 快照：内容哈希去重，幂等不重复落盘 ----
    snapshot = None
    base = product["name"]
    for suffix in ("", "_a", "_b", "_c"):
        cand = os.path.join(layouts_dir, f"{base}{suffix}.json")
        if os.path.exists(cand):
            try:
                with open(cand, "rb") as f:
                    old = f.read()
                if hashlib.sha256(old).hexdigest()[:12] == digest:
                    snapshot = cand
                    break
            except Exception:
                continue
        else:
            snapshot = cand
            break
    if snapshot is None:
        snapshot = os.path.join(layouts_dir, f"{base}_{digest}.json")
    if not os.path.exists(snapshot):
        with open(snapshot, "wb") as f:
            f.write(payload)

    # ---- current.json：原子替换，同输入字节一致 ----
    current = os.path.join(layouts_dir, current_name)
    tmp = current + ".tmp"
    with open(tmp, "wb") as f:
        f.write(payload)
    os.replace(tmp, current)

    return {"ok": True, "snapshot": snapshot, "current": current,
            "message": f"已冻结 {len(buildings)} 个建筑（人工修改 {manual_edits}）",
            "product": product, "errors": []}


# ================================================================ 换算自测辅助

def tile_roundtrip_error(calib, rx, ry):
    """渲染像素 -> 瓦片 -> 渲染像素 -> 瓦片，返回瓦片空间最大往返误差（格）。

    用于自测：同一透视反解的自洽误差应远小于 1 格。
    """
    gx, gy = calib.px_to_tile(rx, ry)
    bx, by = calib.tile_to_px(gx, gy)
    gx2, gy2 = calib.px_to_tile(bx, by)
    return max(abs(gx2 - gx), abs(gy2 - gy))


def bbox_center_tile(calib, bbox):
    """bbox 中心渲染像素 -> [gx, gy]，并给出 tile 往返误差（格）。"""
    cx = (bbox[0] + bbox[2]) / 2.0
    cy = (bbox[1] + bbox[3]) / 2.0
    gx, gy = calib.px_to_tile(cx, cy)
    err = tile_roundtrip_error(calib, cx, cy)
    return [round(gx, 2), round(gy, 2)], err
