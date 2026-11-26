# -*- coding: utf-8 -*-
"""热键流水线：抓帧 → OCR → ClashKing API → 落盘 + 一行文案 + 可选按 TH 回填等级。"""
from __future__ import annotations

import json
import os
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LATEST = "ocr_latest.json"


def latest_path(root=None):
    return os.path.join(root or ROOT, "out", LATEST)


def run_ocr(root, frame_bgr, fresh=True):
    """跑一次识别；返回 payload（同时落盘 out/ocr_latest.json）。异常向上抛。"""
    from . import cocapi, ocr_screen
    got = ocr_screen.read_opponent(frame_bgr)
    api = None
    if got.get("name") or got.get("clan"):
        api = cocapi.resolve_opponent(got.get("name"), got.get("clan"), fresh=fresh,
                                      ocr_level=got.get("level"))
    th = None
    if api and (api.get("player") or {}).get("th"):
        th = int(api["player"]["th"])
    payload = {"ocr": got, "api": api, "th": th,
               "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "fresh": bool(fresh),
               "line": format_line(got, api, th)}
    save(root, payload)
    return payload


def format_line(ocr=None, api=None, th=None):
    """压成面板一行：「对手：MH Tipu（TH15）· 17:02 识别」。"""
    ocr = ocr or {}
    api = api or {}
    p = api.get("player") or {}
    name = p.get("name") or ocr.get("name") or "未知"
    thn = th or p.get("th")
    if not thn and ocr.get("level"):
        thn = str(ocr["level"]).rstrip(".．、本")
    stamp = time.strftime("%H:%M")
    src = "OCR+API" if p.get("tag") else "OCR"
    return "对手：%s（TH%s）· %s %s" % (name, thn if thn else "?", stamp, src)


def save(root, payload):
    path = latest_path(root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    return path


def load(root=None):
    try:
        with open(latest_path(root), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def apply_to_layout(layout, payload):
    """按识别到的 TH 把布局建筑等级回填到副本；返回 (新副本, 更新数)。"""
    if not isinstance(layout, dict) or not payload:
        return layout, 0
    th = payload.get("th")
    if not th:
        return layout, 0
    from . import cocapi
    doc = json.loads(json.dumps(layout, ensure_ascii=False))
    res = cocapi.apply_th_levels(doc, int(th))
    return doc, int(res.get("updated") or 0)
