# -*- coding: utf-8 -*-
"""覆盖层 PANEL 数据层：路径 + mtime 侦测 + 归一化 + 缺文件降级。

铁律：
  * 任何文件缺失、JSON 损坏、字段缺项都不得抛异常，返回降级空壳并带 error 说明；
  * 本层只读，不写任何业务文件（冻结产物由 editor.py 负责）；
  * 中文路径图片一律 cv2.imdecode(np.fromfile(...))，不用 cv2.imread；
  * 坐标换算一律走 clashlab.geo.Calib，本层不做第二套换算。

研究页消费的文件（识别线/研究线稍后产出，缺失即显示「待产出」）：
  out/study/study.png            研究图（俯视网格报告图，1560x1006 或识别线自定）
  out/study/study.json           研究报告（layout/army/report/plans）
  out/prebattle/brief.md         赛前简报（最新一份，历史副本在 out/audit/ 勿误用）
  out/prebattle/info.json        赛前情报（th/defense_counts/exposed/blind/unknown）
  out/overlay/layout_candidates.json  识别候选（识别线产出，可缺）
  out/overlay/overlay.png        候选框已画好的底图（识别线产出，可缺；缺则用原始截图）

设置页：
  config/overlay.json            热键表 + 贴合偏移（运行时线独占写，本层只读）
  config/anchors.json            锚点覆盖表（与内置实测表合并）
采集页：
  out/farm/farm_report.json      farm 只读状态（不实例化 Farm，不连 adb）
  out/overlay/clicks.log          最近点击日志尾部（可缺）
"""
import json
import os
import sys
import time

# 中文路径读图（不依赖 imread；numpy/cv2 已在环境内，import 失败时 image_meta 降级）
try:
    import numpy as np
    import cv2
except Exception:  # pragma: no cover
    np = None
    cv2 = None


# ---------------------------------------------------------------- 路径解析

_ROOT_MARKERS = ("config/anchors.json", "out/prebattle", "clashlab/geo.py")


def _looks_like_root(d):
    if not d or not os.path.isdir(d):
        return False
    return any(os.path.exists(os.path.join(d, m)) for m in _ROOT_MARKERS)


def resolve_root():
    """项目根（P0-1 两级兜底，禁回退 C:\\Users）：
    1) CLASHLAB_ROOT 环境变量；
    2) 冻结产物：exe 同目录 → %LOCALAPPDATA%\\ClashOverlay；都无锚点仍回 exe 同目录，
       由面板出中文缺数据提示；
    3) 源码：本文件上两级（clashlab/overlay -> 项目根）。"""
    env = os.environ.get("CLASHLAB_ROOT")
    if env and os.path.isdir(env):
        return os.path.abspath(env)
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        if _looks_like_root(exe_dir):
            return exe_dir
        lad = os.path.join(os.environ.get("LOCALAPPDATA", ""), "ClashOverlay")
        if lad and os.path.isdir(lad) and _looks_like_root(lad):
            return os.path.abspath(lad)
        return exe_dir  # 无锚点：界面中文提示，不回退用户主目录
    here = os.path.dirname(os.path.abspath(__file__))
    # clashlab/overlay/data.py -> clashlab -> 项目根
    return os.path.abspath(os.path.join(here, "..", ".."))


def has_data(root):
    """root 下是否存在任一业务锚点（config/ 或 out/），供面板缺数据提示。"""
    if not root:
        return False
    return any(os.path.exists(os.path.join(root, rel))
               for rel in ("config/anchors.json", "config/overlay.json",
                           "out/prebattle", "out/marks/marks.json",
                           "out/study/study.json"))


class Paths:
    """集中登记所有消费文件，相对项目根；全部允许缺失。"""

    def __init__(self, root=None):
        self.root = os.path.abspath(root or resolve_root())

    def p(self, rel):
        return os.path.join(self.root, rel.replace("/", os.sep))

    # 研究页
    @property
    def study_png(self):
        return self.p("out/study/study.png")

    @property
    def study_json(self):
        return self.p("out/study/study.json")

    @property
    def brief_md(self):
        return self.p("out/prebattle/brief.md")

    @property
    def info_json(self):
        return self.p("out/prebattle/info.json")

    @property
    def candidates_json(self):
        return self.p("out/overlay/layout_candidates.json")

    @property
    def overlay_png(self):
        return self.p("out/overlay/overlay.png")

    # 设置页
    @property
    def overlay_config(self):
        return self.p("config/overlay.json")

    @property
    def anchors_json(self):
        return self.p("config/anchors.json")

    # 采集页
    @property
    def farm_report(self):
        return self.p("out/farm/farm_report.json")

    @property
    def clicks_log(self):
        return self.p("out/overlay/clicks.log")

    # 冻结产物目录（读目录列表用；写入由 editor.py 完成）
    @property
    def layouts_dir(self):
        return self.p("layouts")


# ---------------------------------------------------------------- 基础读取

def file_info(path):
    """存在性/mtime/大小，任何异常都返回 exists=False，不抛。"""
    info = {"path": path, "exists": False, "mtime": None, "size": None, "error": None}
    try:
        if path and os.path.exists(path):
            st = os.stat(path)
            info["exists"] = True
            info["mtime"] = st.st_mtime
            info["size"] = st.st_size
    except Exception as e:  # pragma: no cover
        info["error"] = str(e)
    return info


def load_json(path, default=None):
    """读 JSON。缺失 -> (default, 'missing')；损坏 -> (default, 错误串)；成功 -> (data, None)。"""
    if not path or not os.path.exists(path):
        return default, "missing"
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f), None
    except Exception as e:
        return default, f"json_parse_error: {e}"


def load_text(path):
    """读纯文本（brief.md 等）。缺失/损坏 -> ('', 错误串)。"""
    if not path or not os.path.exists(path):
        return "", "missing"
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read(), None
    except Exception as e:
        return "", f"text_read_error: {e}"


def image_meta(path):
    """只取图片尺寸与编码信息，不解纹理。中文路径走 imdecode。失败降级。"""
    info = file_info(path)
    info.update({"w": None, "h": None, "decodable": False})
    if not info["exists"] or np is None or cv2 is None:
        return info
    try:
        buf = np.fromfile(path, dtype=np.uint8)
        img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
        if img is not None:
            info["h"], info["w"] = int(img.shape[0]), int(img.shape[1])
            info["decodable"] = True
    except Exception as e:
        info["error"] = f"image_decode_error: {e}"
    return info


# ---------------------------------------------------------------- marks.json 归一化

def normalize_marks(raw):
    """out/marks/marks.json 归一化。

    输入缺项/坏条目一律跳过；返回固定骨架，UI 永远能渲染空表。
    保留原始字段，UI 可按需取。
    """
    out = {"version": None, "source": None, "marks": [], "pins": [],
           "circles": [], "lines": [], "steps": [], "cards": [],
           "profile": {}, "prebattle": {}, "error": None}
    if not isinstance(raw, dict):
        out["error"] = "marks_not_dict"
        return out
    out["version"] = raw.get("version")
    out["source"] = raw.get("source")
    for key, dst in (("marks", "marks"), ("pins", "pins"),
                     ("circles", "circles"), ("lines", "lines")):
        rows = raw.get(key) or []
        if not isinstance(rows, list):
            continue
        for row in rows:
            if isinstance(row, dict):
                out[dst].append(row)
    steps = raw.get("steps") or []
    out["steps"] = [s for s in steps if isinstance(s, str)] if isinstance(steps, list) else []
    out["cards"] = [c for c in (raw.get("cards") or []) if isinstance(c, str)]
    if isinstance(raw.get("profile"), dict):
        out["profile"] = raw["profile"]
    if isinstance(raw.get("prebattle"), dict):
        out["prebattle"] = raw["prebattle"]
    return out


def load_marks(path):
    """读 out/marks/marks.json -> (归一化骨架, file_info)。"""
    info = file_info(path)
    raw, err = load_json(path)
    data = normalize_marks(raw)
    if err:
        data["error"] = err
    return data, info


# ---------------------------------------------------------------- layout_candidates.json 归一化
#
# 识别线产出契约（本层按此兼容，缺字段降级）：
# {
#   "version": 1,
#   "source": "原始截图路径或标识",
#   "image": "overlay.png",
#   "quad": [[x0,y0],[x1,y1],[x2,y2],[x3,y3]],   # 可选，渲染坐标系 1280x720
#   "candidates": [
#     {"id": "c0", "label": "air-defense", "type": "air-defense",
#      "bbox": [x0, y0, x1, y1],                 # 渲染坐标，两对角点
#      "box": [x, y, w, h],                      # 兼容检测线 (x,y,w,h) 形式
#      "confidence": 0.87, "score": 0.87,        # confidence/score 别名
#      "tile": [22, 32]}
#   ]
# }

def _to_bbox(row):
    """把 bbox=[x0,y0,x1,y1] 或 box=[x,y,w,h] 统一成 [x0,y0,x1,y1]，非法返回 None。"""
    bbox = row.get("bbox")
    if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
        try:
            x0, y0, x1, y1 = [float(v) for v in bbox]
        except (TypeError, ValueError):
            return None
    else:
        box = row.get("box")
        if isinstance(box, (list, tuple)) and len(box) == 4:
            try:
                x, y, w, h = [float(v) for v in box]
                x0, y0, x1, y1 = x, y, x + w, y + h
            except (TypeError, ValueError):
                return None
        else:
            return None
    if x1 < x0:
        x0, x1 = x1, x0
    if y1 < y0:
        y0, y1 = y1, y0
    if x1 - x0 < 1 or y1 - y0 < 1:
        return None
    return [x0, y0, x1, y1]


def normalize_candidates(raw):
    """识别候选归一化。缺文件/坏 JSON -> candidates=[] 且 present=False。"""
    out = {"version": None, "source": None, "image": None, "quad": None,
           "candidates": [], "present": False, "error": None}
    if not isinstance(raw, dict):
        out["error"] = "candidates_not_dict"
        return out
    out["version"] = raw.get("version")
    out["source"] = raw.get("source")
    out["image"] = raw.get("image")
    quad = raw.get("quad")
    if isinstance(quad, list) and len(quad) == 4:
        out["quad"] = [[float(p[0]), float(p[1])] for p in quad if isinstance(p, (list, tuple)) and len(p) >= 2]
    rows = raw.get("candidates") or []
    if not isinstance(rows, list):
        rows = []
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        bbox = _to_bbox(row)
        if bbox is None:
            continue
        conf = row.get("confidence")
        if conf is None:
            conf = row.get("score")
        try:
            conf = float(conf) if conf is not None else 0.0
        except (TypeError, ValueError):
            conf = 0.0
        tile = row.get("tile")
        if isinstance(tile, (list, tuple)) and len(tile) == 2:
            tile = [float(tile[0]), float(tile[1])]
        cid = row.get("id") or f"c{i}"
        out["candidates"].append({
            "id": str(cid),
            "label": str(row.get("label") or row.get("type") or "未命名"),
            "type": row.get("type") or row.get("label") or "unknown",
            "bbox": bbox,
            "confidence": max(0.0, min(1.0, conf)),
            "tile": tile,
            "hidden": False,
            "selected": False,
            "manual": False,
            "edit": "kept",
        })
    out["present"] = bool(out["candidates"])
    # 按置信度降序（研究页列表直接用）
    out["candidates"].sort(key=lambda c: -c["confidence"])
    return out


def load_candidates(path):
    raw, err = load_json(path)
    data = normalize_candidates(raw)
    info = file_info(path)
    if err:
        data["error"] = err
    return data, info


# ---------------------------------------------------------------- 研究包（study/brief/info）

def load_study_pack(paths):
    """研究页视图数据：study.png/study.json/brief.md/info.json 各自独立降级。"""
    pack = {
        "study_png": image_meta(paths.study_png),
        "study_json": {"info": file_info(paths.study_json), "data": None, "error": None},
        "brief": {"info": file_info(paths.brief_md), "text": "", "error": None},
        "info": {"info": file_info(paths.info_json), "data": None, "error": None},
    }
    raw, err = load_json(paths.study_json)
    if err:
        pack["study_json"]["error"] = err
    else:
        pack["study_json"]["data"] = raw
    text, err = load_text(paths.brief_md)
    pack["brief"]["text"] = text
    if err:
        pack["brief"]["error"] = err
    raw, err = load_json(paths.info_json)
    if err:
        pack["info"]["error"] = err
    else:
        pack["info"]["data"] = raw
    return pack


# ---------------------------------------------------------------- 锚点表
#
# 内置实测锚点（1280x720 渲染坐标，hint 实测口径；config/anchors.json 可覆盖合并）。
# confirmed=False 的候选（scout_back/scout_attack）设置页必须标「未验证」，禁止当已确认。
BUILTIN_ANCHORS = {
    "store": {"point": [1170, 645], "confirmed": True,
              "note": "商店按钮（hint 实测坐标）", "evidence": []},
    "battle": {"point": [88, 645], "confirmed": True,
               "note": "夜世界主页左下“战斗”按钮",
               "evidence": ["out/farm/probe/02_battle_open_before.png",
                            "out/farm/probe/03_battle_open_after.png"]},
    "m_battle": {"point": [75, 635], "confirmed": True,
                 "note": "主村主页左下“战斗”按钮",
                 "evidence": ["out/farm/probe/45_mhome_battle2_before.png",
                              "out/farm/probe/46_mhome_battle2_after.png"]},
    "m_search": {"point": [197, 535], "confirmed": True,
                 "note": "主村常规战卡片“搜索对手 1500”按钮",
                 "evidence": ["out/farm/probe/55_search3_before.png",
                              "out/farm/probe/56_search3_after.png"]},
    "attack_close": {"point": [1088, 133], "confirmed": True,
                     "note": "开始进攻面板右上红色关闭X",
                     "evidence": ["out/farm/probe/73_attack_close_before.png",
                                  "out/farm/probe/74_attack_close_after.png"]},
    "confirm_close": {"point": [1237, 90], "confirmed": True,
                      "note": "我的军队开战确认面板右上关闭X（绝不点绿色“进攻！”）",
                      "evidence": ["out/farm/probe/56_search3_after.png",
                                   "out/farm/probe/77_state.png"]},
    "find": {"point": [951, 474], "confirmed": True,
             "note": "开始进攻面板右下绿色“立即寻找！”按钮",
             "evidence": ["out/farm/probe/05_find_crop.png"]},
    "edit_army": {"point": [421, 570], "confirmed": True,
                  "note": "开始进攻面板左下绿色“编辑军队”按钮",
                  "evidence": ["out/farm/probe/07_edit_army_before.png",
                               "out/farm/probe/08_edit_army_after.png"]},
    "scout_back": {"point": [64, 44], "confirmed": False,
                   "note": "侦察界面左上返回（候选坐标，未实测）", "evidence": []},
    "scout_attack": {"point": [1150, 640], "confirmed": False,
                     "note": "侦察界面右下红色进攻（候选坐标，未实测；红线禁止点）", "evidence": []},
}


def load_anchors(paths):
    """合并内置实测表与 config/anchors.json（只读覆盖，不回写）。

    返回 [{key, point, confirmed, note, evidence, source}]，已确认在前。
    """
    rows = {}
    for k, v in BUILTIN_ANCHORS.items():
        rows[k] = {"key": k, "point": list(v["point"]), "confirmed": bool(v["confirmed"]),
                   "note": v.get("note", ""), "evidence": list(v.get("evidence", [])),
                   "source": "builtin"}
    raw, err = load_json(paths.anchors_json)
    if isinstance(raw, dict):
        for k, v in raw.items():
            if not isinstance(v, dict):
                if isinstance(v, (list, tuple)) and len(v) == 2:
                    rows[k] = {"key": k, "point": [int(v[0]), int(v[1])],
                               "confirmed": False, "note": "", "evidence": [], "source": "anchors.json"}
                continue
            merged = dict(rows.get(k, {"key": k, "point": [0, 0], "confirmed": False,
                                       "note": "", "evidence": [], "source": "anchors.json"}))
            merged.update({kk: vv for kk, vv in v.items() if kk in ("point", "confirmed", "note", "evidence")})
            if isinstance(v.get("point"), (list, tuple)) and len(v["point"]) == 2:
                merged["point"] = [int(v["point"][0]), int(v["point"][1])]
            merged["confirmed"] = bool(merged.get("confirmed", False))
            merged["source"] = "anchors.json"
            rows[k] = merged
    out = list(rows.values())
    out.sort(key=lambda r: (not r["confirmed"], r["key"]))
    return {"anchors": out, "error": err, "info": file_info(paths.anchors_json)}


# ---------------------------------------------------------------- overlay.json（只读）

def load_overlay_config(paths):
    """读 config/overlay.json（运行时线独占写，本层只读）。

    热键表归一化为 [{keys, action, desc}]；缺文件 -> 空表 + error='missing'。
    贴合偏移 dx/dy 单独给出，缺省 0。
    """
    cfg = {"hotkeys": [], "offset": {"dx": 0.0, "dy": 0.0}, "error": None,
           "info": file_info(paths.overlay_config), "raw": None}
    raw, err = load_json(paths.overlay_config)
    if err:
        cfg["error"] = err
        return cfg
    cfg["raw"] = raw
    if isinstance(raw, dict):
        off = raw.get("offset") or raw.get("fit_offset") or {}
        if isinstance(off, dict):
            try:
                cfg["offset"]["dx"] = float(off.get("dx", 0) or 0)
                cfg["offset"]["dy"] = float(off.get("dy", 0) or 0)
            except (TypeError, ValueError):
                pass
        hk = raw.get("hotkeys") or raw.get("keys") or []
        if isinstance(hk, dict):
            hk = [{"keys": k, "action": a} for k, a in hk.items()]
        if isinstance(hk, list):
            for row in hk:
                if isinstance(row, dict):
                    cfg["hotkeys"].append({
                        "keys": row.get("keys") or row.get("key") or "",
                        "action": row.get("action") or row.get("cmd") or "",
                        "desc": row.get("desc") or row.get("description") or "",
                    })
    return cfg


# ---------------------------------------------------------------- 采集页

def load_farm_report(paths):
    """只读 out/farm/farm_report.json（不实例化 Farm、不连 adb）。缺文件降级。"""
    rep = {"mode": None, "live": None, "dry_run": None, "stats": {}, "blockers": [],
           "anchors_table": [], "timestamp": None, "error": None,
           "info": file_info(paths.farm_report)}
    raw, err = load_json(paths.farm_report)
    if err:
        rep["error"] = err
        return rep
    if isinstance(raw, dict):
        rep["mode"] = raw.get("mode")
        rep["live"] = bool(raw.get("live"))
        rep["dry_run"] = not rep["live"] if rep["live"] is not None else True
        rep["stats"] = raw.get("stats") or {}
        rep["blockers"] = [b for b in (raw.get("blockers") or []) if isinstance(b, str)]
        rep["timestamp"] = raw.get("timestamp")
        for row in raw.get("anchors") or []:
            if isinstance(row, dict):
                rep["anchors_table"].append(row)
    return rep


def read_clicks_tail(path, n=40):
    """读点击日志尾部 n 行；缺文件/损坏 -> ([], error)。"""
    info = file_info(path)
    if not info["exists"]:
        return [], "missing"
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
        return lines[-n:], None
    except Exception as e:
        return [], f"clicks_read_error: {e}"


# ---------------------------------------------------------------- 汇总视图（供 pages.py 取数）

def load_panel_view(paths=None):
    """一次性给三页取数；任何子项失败都不影响其余。"""
    paths = paths or Paths()
    marks, marks_info = load_marks(paths.p("out/marks/marks.json"))
    candidates, cand_info = load_candidates(paths.candidates_json)
    return {
        "paths": {k: getattr(paths, k) for k in dir(paths) if not k.startswith("_") and isinstance(getattr(paths, k), str)},
        "marks": marks, "marks_info": marks_info,
        "candidates": candidates, "candidates_info": cand_info,
        "study": load_study_pack(paths),
        "anchors": load_anchors(paths),
        "overlay_config": load_overlay_config(paths),
        "farm": load_farm_report(paths),
        "clicks": read_clicks_tail(paths.clicks_log),
        "now": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
