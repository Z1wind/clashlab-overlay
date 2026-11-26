# -*- coding: utf-8 -*-
"""四角标注服务：给每个阵图点出地图四角（上/右/下/左），存 out/corners/<file>.json。

    python tools/label_corners/start.py            # http://127.0.0.1:8781
    python tools/label_corners/start.py --port 8800 --no-open
"""
from __future__ import annotations

import argparse
import json
import os
import re
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
IMG_DIRS = [os.path.join(ROOT, "out", "sceneries")]
BASE_DIR = os.path.join(ROOT, "bases")
CORNER_DIR = os.path.join(ROOT, "out", "corners")
IMAGE_EXT = (".jpg", ".jpeg", ".png", ".webp")
SKIP = ("_meta.json",)


def discover():
    items = []
    for d in IMG_DIRS:
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if fn.lower().endswith(IMAGE_EXT):
                items.append(os.path.join(d, fn))
    # 已有阵的 base.png 也加入（不同皮肤）
    if os.path.isdir(BASE_DIR):
        for th in sorted(os.listdir(BASE_DIR)):
            th_dir = os.path.join(BASE_DIR, th)
            if not os.path.isdir(th_dir):
                continue
            for bid in sorted(os.listdir(th_dir)):
                p = os.path.join(th_dir, bid, "base.png")
                if os.path.exists(p):
                    items.append(p)
    out = []
    for p in items:
        name = os.path.relpath(p, ROOT).replace(os.sep, "/")
        safe = re.sub(r"[^A-Za-z0-9_.-]", "_", name)
        cpath = os.path.join(CORNER_DIR, safe + ".json")
        done = os.path.exists(cpath)
        display = name.split("/")[-2] + "/" + os.path.basename(p) if "bases/" in name else os.path.basename(p)
        out.append({"file": name, "name": display, "done": done,
                    "corner_id": safe, "size": os.path.getsize(p)})
    return out


class Handler(BaseHTTPRequestHandler):
    server_version = "CornerLabel/1.0"

    def log_message(self, fmt, *args):
        print("[corners] " + (fmt % args), flush=True)

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False))

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if u.path in ("/", "/index.html"):
            p = os.path.join(HERE, "index.html")
            self._send(200, open(p, "rb").read(), "text/html; charset=utf-8")
        elif u.path == "/api/list":
            self._json({"ok": True, "items": discover()})
        elif u.path == "/api/progress":
            items = discover()
            done = sum(1 for i in items if i["done"])
            self._json({"ok": True, "total": len(items), "done": done})
        elif u.path == "/img":
            rel = q.get("f", [""])[0]
            p = os.path.abspath(os.path.join(ROOT, rel))
            if not (p.startswith(ROOT) and os.path.exists(p)):
                return self._json({"ok": False, "error": "not found"}, 404)
            data = open(p, "rb").read()
            ctype = "image/png" if p.lower().endswith(".png") else "image/jpeg"
            self._send(200, data, ctype)
        else:
            self._json({"ok": False, "error": "未知路径"}, 404)

    def do_POST(self):
        u = urlparse(self.path)
        try:
            n = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(n).decode("utf-8-sig") or "{}")
        except Exception:
            return self._json({"ok": False, "error": "JSON 解析失败"}, 400)
        if u.path == "/api/save":
            file = str(body.get("file") or "")
            quad = body.get("quad")
            err = []
            if not file or ".." in file:
                err.append("file 非法")
            if not isinstance(quad, list) or len(quad) != 4:
                err.append("quad 必须是 4 个点")
            else:
                for i, pt in enumerate(quad):
                    if not (isinstance(pt, (list, tuple)) and len(pt) == 2):
                        err.append("quad[%d] 非法" % i)
            if err:
                return self._json({"ok": False, "error": "；".join(err)}, 400)
            os.makedirs(CORNER_DIR, exist_ok=True)
            safe = re.sub(r"[^A-Za-z0-9_.-]", "_", file)
            p = os.path.join(CORNER_DIR, safe + ".json")
            doc = {"file": file, "quad": [[round(float(x), 2), round(float(y), 2)] for x, y in quad],
                   "order": ["top", "right", "bottom", "left"],
                   "saved_at": __import__("datetime").datetime.now().astimezone().isoformat(timespec="seconds")}
            tmp = p + ".tmp"
            open(tmp, "w", encoding="utf-8").write(json.dumps(doc, ensure_ascii=False, indent=1))
            os.replace(tmp, p)
            self._json({"ok": True, "saved": os.path.relpath(p, ROOT).replace(os.sep, "/"), "doc": doc})
        else:
            self._json({"ok": False, "error": "未知路径"}, 404)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8781)
    ap.add_argument("--no-open", action="store_true")
    a = ap.parse_args()
    os.makedirs(CORNER_DIR, exist_ok=True)
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    url = "http://127.0.0.1:%d/" % a.port
    print("四角标注服务: " + url + "  (Ctrl+C 退出)", flush=True)
    print("图片目录: out/sceneries + bases/**/base.png；结果写 out/corners/", flush=True)
    if not a.no_open:
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
