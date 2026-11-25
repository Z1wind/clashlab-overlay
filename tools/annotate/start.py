# -*- coding: utf-8 -*-
"""TH16 阵型标注工具 —— 本地 HTTP 服务（纯标准库，零第三方依赖）。

用法（在项目根目录，或任意目录都行，脚本自己定位根目录）：
    python tools/annotate/start.py                 # 默认 127.0.0.1:8765，自动开浏览器
    python tools/annotate/start.py --port 9000 --no-open
    python tools/annotate/start.py --root <含 bases 的目录>

页面：单文件 index.html（内联 CSS/JS，无 npm）。
数据：读 bases/<th>/NN/{base.png,layout.json}（+ 可选 layouts/*.json 候选方案），
      人工结果写 out/annotate/NN_annotated.json（与 layout.json 同 schema）
      + out/annotate/summary.json（每阵：建筑数 / 人工修改次数 / 耗时 / 状态）。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import traceback
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import annotate_core as core  # noqa: E402

INDEX_PATH = os.path.join(HERE, "index.html")
DEFAULT_ROOT = os.path.dirname(os.path.dirname(HERE))   # tools/annotate -> 项目根
MAX_BODY_BYTES = 8 * 1024 * 1024
_PNG_SIG = b"\x89PNG\r\n\x1a\n"
_TH_RE = re.compile(r"^th\d+$")
_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")


class AppError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


def _rel(path):
    return str(path).replace(os.sep, "/")


class App(object):
    """无状态业务层：每次请求现读磁盘（数据量小，避免缓存不一致）。"""

    def __init__(self, root):
        self.root = os.path.abspath(root)

    # ---- 发现 / 查找 ----
    def groups(self):
        return core.discover_groups(self.root)

    def find_base(self, th, bid):
        if not th or not bid:
            raise AppError(400, "缺少 th / id 参数")
        if not _TH_RE.match(str(th)):
            raise AppError(400, "th 参数非法：%r" % (th,))
        if not _ID_RE.match(str(bid)):
            raise AppError(400, "id 参数非法：%r" % (bid,))
        for g in self.groups():
            if g["th"] != th:
                continue
            for b in g["bases"]:
                if b["id"] == bid:
                    return g, b
        raise AppError(404, "找不到阵：%s/%s" % (th, bid))

    def candidate_path(self, base, cand_id):
        if not cand_id or cand_id == "layout":
            return base["layout"], "layout"
        for c in base["candidates"]:
            if c["id"] == cand_id:
                return c["path"], c["id"]
        raise AppError(404, "找不到候选方案：%s" % cand_id)

    def palette(self):
        out = []
        for idx, t in enumerate(core.PALETTE):
            out.append({
                "type": t,
                "cn": core.type_cn(t),
                "size": core.type_size(t),
                "hotkey": (idx + 1) if idx < core.PALETTE_HOTKEY_COUNT else None,
            })
        return out

    # ---- GET /api/state ----
    def state_payload(self):
        groups = self.groups()
        summary = core.load_summary(core.summary_path(self.root))
        smap = {(e.get("th"), e.get("base")): e for e in summary.get("bases", [])}
        out_groups = []
        for g in groups:
            bases = []
            for b in g["bases"]:
                entry = smap.get((g["th"], b["id"]))
                bases.append({
                    "th": g["th"],
                    "id": b["id"],
                    "label": b["label"],
                    "layout_name": b["layout_name"],
                    "prefilled": b["prefilled"],
                    "grid": b["grid"],
                    "has_quad": bool(b.get("has_quad", True)),
                    "candidates": [{"id": c["id"], "title": c["title"], "source": c["source"]}
                                   for c in b["candidates"]],
                    "annotated": {
                        "exists": bool(b["annotated"]["exists"]),
                        "buildings": int(b["annotated"]["buildings"]),
                        "updated_at": b["annotated"]["updated_at"],
                    },
                    "summary": ({k: entry.get(k) for k in
                                 ("status", "manual_edits", "buildings", "elapsed_ms",
                                  "updated_at", "candidate")} if entry else None),
                })
            out_groups.append({"th": g["th"], "label": g["label"], "bases": bases})
        return {
            "ok": True,
            "root_name": os.path.basename(self.root),
            "groups": out_groups,
            "summary": summary,
            "palette": self.palette(),
            "paths": {
                "annotated_dir": _rel(core.OUT_DIR_REL),
                "summary": _rel(core.summary_rel_path()),
            },
        }

    # ---- GET /api/base ----
    def base_payload(self, th, bid, candidate=None):
        g, base = self.find_base(th, bid)
        if not base.get("has_quad"):
            raise AppError(400, "该阵 layout.json 的 note 里没有可用 quad 定标，无法建立像素↔tile 映射："
                            + base["layout"])
        layout_doc = core.load_json(base["layout"])
        if not isinstance(layout_doc, dict):
            raise AppError(500, "读不到 layout.json：%s" % base["layout"])
        cand_id = str(candidate or "layout")
        cand_path, cand_key = self.candidate_path(base, cand_id)
        cand_doc = core.load_json(cand_path)
        if not isinstance(cand_doc, dict):
            raise AppError(500, "候选方案不可读：%s" % cand_path)
        annotated_path = core.annotated_path(self.root, bid)
        annotated_doc = core.load_json(annotated_path)
        if cand_key == "layout":
            # 默认方案：已标注过则续编辑（保留上次人工结果）
            prefill, prefill_source = core.resolve_prefill(cand_doc, annotated_doc)
        else:
            # 候选方案不与默认方案的标注混用
            prefill, prefill_source = core.resolve_prefill(cand_doc, None)
        override_quad = core.load_override_quad(self.root, bid)
        geo = (core.geometry_for_layout(cand_doc, override_quad)
               or core.geometry_for_layout(layout_doc, override_quad))
        if geo is None:
            raise AppError(400, "该阵 quad 无法求解单应矩阵（四点共线或格式异常）")
        size = core.image_size(base["image"])
        if size is None:
            raise AppError(500, "读不到 base.png 尺寸（仅支持 PNG/JPEG）：%s" % base["image"])
        try:
            mtime = int(os.stat(base["image"]).st_mtime_ns)
        except OSError:
            mtime = 0
        summary = core.load_summary(core.summary_path(self.root))
        entry = next((e for e in summary.get("bases", [])
                      if e.get("th") == th and e.get("base") == bid), None)
        return {
            "ok": True,
            "th": th,
            "id": bid,
            "label": base["label"],
            "layout_name": base["layout_name"],
            "grid": geo["grid"],
            "quad": geo["quad"],
            "quad_source": geo.get("quad_source", "layout"),
            "layout_quad": core.parse_quad(layout_doc.get("note") or ""),
            "override_quad": override_quad,
            "quad_url": "/api/quad?th=%s&id=%s" % (urllib.parse.quote(th), urllib.parse.quote(bid)),
            "H": geo["H"],
            "Hinv": geo["Hinv"],
            "image_url": "/img?th=%s&id=%s&v=%d" % (urllib.parse.quote(th), urllib.parse.quote(bid), mtime),
            "image_size": [size[0], size[1]],
            "doc": prefill,
            "prefill_source": prefill_source,
            "candidate": cand_key,
            "candidates": [{"id": c["id"], "title": c["title"], "source": c["source"]}
                           for c in base["candidates"]],
            "annotated": {
                "exists": isinstance(annotated_doc, dict),
                "updated_at": (core._mtime_iso(annotated_path)
                               if isinstance(annotated_doc, dict) else ""),
            },
            "summary_entry": entry,
            "palette": self.palette(),
            "paths": {
                "annotated": _rel(core.annotated_rel_path(bid)),
                "summary": _rel(core.summary_rel_path()),
            },
        }

    # ---- POST /api/save ----
    def save_payload(self, body):
        if not isinstance(body, dict):
            raise AppError(400, "请求体必须是 JSON 对象")
        th = str(body.get("th") or "")
        bid = str(body.get("id") or "")
        g, base = self.find_base(th, bid)
        cand_id = str(body.get("candidate") or "layout")
        if cand_id != "layout":
            self.candidate_path(base, cand_id)      # 仅校验候选存在
        doc = body.get("doc")
        if not isinstance(doc, dict):
            raise AppError(400, "doc 必须是 layout 对象")
        layout_doc = core.load_json(base["layout"])
        if not isinstance(layout_doc, dict):
            raise AppError(500, "读不到 layout.json：%s" % base["layout"])
        errors = core.validate_layout(doc, grid=base.get("grid"))
        if errors:
            more = " …（共 %d 处）" % len(errors) if len(errors) > 6 else ""
            raise AppError(400, "schema 校验失败：" + "；".join(errors[:6]) + more)
        normalized = core.normalize_layout(doc, grid=base.get("grid"))
        baseline = core.normalize_layout(layout_doc, grid=base.get("grid"))
        diff = core.diff_layout(baseline, normalized)
        override_quad = core.load_override_quad(self.root, bid)
        quad_source = "override" if override_quad is not None else "layout"
        normalized["note"] = core.with_provenance(normalized.get("note", ""), diff["edits"],
                                                  cand_id, quad_source=quad_source)
        annotated_path = core.annotated_path(self.root, bid)
        core.write_json_atomic(annotated_path, normalized)
        elapsed = body.get("elapsed_ms") or 0
        try:
            elapsed = int(elapsed)
        except (TypeError, ValueError):
            elapsed = 0
        skipped = bool(body.get("skipped"))
        status = "skipped" if skipped else "done"
        entry = core.make_summary_entry(bid, th, normalized, diff, elapsed,
                                        status=status, candidate=cand_id)
        summary_path = core.summary_path(self.root)
        summary = core.upsert_summary(core.load_summary(summary_path), entry)
        core.write_json_atomic(summary_path, summary)
        return {
            "ok": True,
            "saved": _rel(core.annotated_rel_path(bid)),
            "quad_source": quad_source,
            "diff": diff,
            "entry": entry,
            "totals": summary["totals"],
            "saved_at": core.now_iso(),
        }

    def summary_payload(self):
        return {"ok": True, "summary": core.load_summary(core.summary_path(self.root))}

    # ---- GET /api/quad（网格校准：当前生效 quad + 来源）----
    def quad_payload(self, th, bid):
        g, base = self.find_base(th, bid)
        layout_doc = core.load_json(base["layout"])
        if not isinstance(layout_doc, dict):
            raise AppError(500, "读不到 layout.json：%s" % base["layout"])
        layout_quad = core.parse_quad(layout_doc.get("note") or "")
        override = core.load_override_quad(self.root, bid)
        quad, source = core.effective_quad(layout_doc, override)
        return {
            "ok": True, "th": th, "id": bid,
            "quad": quad,
            "source": source,
            "layout_quad": layout_quad,
            "override_exists": override is not None,
            "override_path": _rel(core.override_quad_rel_path(bid)),
        }

    # ---- POST /api/quad（保存校准覆盖）----
    def save_quad(self, body):
        if not isinstance(body, dict):
            raise AppError(400, "请求体必须是 JSON 对象")
        th = str(body.get("th") or "")
        bid = str(body.get("id") or "")
        g, base = self.find_base(th, bid)
        size = core.image_size(base["image"])
        try:
            result = core.save_override_quad(self.root, bid, body.get("quad"), image_size=size)
        except ValueError as exc:
            raise AppError(400, str(exc))
        return {
            "ok": True, "th": th, "id": bid,
            "quad": result["quad"],
            "source": "override",
            "saved_at": result["saved_at"],
            "path": _rel(core.override_quad_rel_path(bid)),
            "image_size": list(size) if size else None,
        }

    # ---- DELETE /api/quad（重置为 layout.json 默认）----
    def delete_quad(self, th, bid):
        self.find_base(th, bid)
        removed = core.delete_override_quad(self.root, bid)
        payload = self.quad_payload(th, bid)
        payload["removed"] = removed
        return payload


class AnnotateServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, addr, app):
        self.app = app
        super().__init__(addr, Handler)


class Handler(BaseHTTPRequestHandler):
    server_version = "ClashAnnotate/1.0"

    # ---- 输出 ----
    def _send(self, status, body, ctype="application/json; charset=utf-8", headers=None):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

    def _json(self, status, obj):
        self._send(status, json.dumps(obj, ensure_ascii=False).encode("utf-8"))

    def _error(self, status, msg):
        self._json(status, {"ok": False, "error": msg})

    def log_message(self, fmt, *args):
        sys.stderr.write("[annotate] %s %s\n" % (self.address_string(), fmt % args))

    # ---- 请求 ----
    def _query(self):
        parts = urllib.parse.urlsplit(self.path)
        return parts.path, urllib.parse.parse_qs(parts.query)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        path, q = self._query()
        try:
            if path in ("/", "/index.html"):
                return self._serve_index()
            if path == "/api/health":
                return self._json(200, {"ok": True, "root": self.server.app.root})
            if path == "/api/state":
                return self._json(200, self.server.app.state_payload())
            if path == "/api/base":
                return self._json(200, self.server.app.base_payload(
                    self._q1(q, "th"), self._q1(q, "id"), self._q1(q, "candidate")))
            if path == "/api/summary":
                return self._json(200, self.server.app.summary_payload())
            if path == "/api/quad":
                return self._json(200, self.server.app.quad_payload(
                    self._q1(q, "th"), self._q1(q, "id")))
            if path == "/img":
                return self._serve_image(self._q1(q, "th"), self._q1(q, "id"))
            if path == "/favicon.ico":
                return self._send(204, b"")
            return self._error(404, "未知路径：%s" % path)
        except AppError as e:
            return self._error(e.status, e.message)
        except Exception:
            traceback.print_exc()
            return self._error(500, "服务器内部错误（看控制台 traceback）")

    def do_POST(self):
        path, _q = self._query()
        try:
            if path == "/api/save":
                body = self._read_body()
                return self._json(200, self.server.app.save_payload(body))
            if path == "/api/quad":
                body = self._read_body()
                return self._json(200, self.server.app.save_quad(body))
            return self._error(404, "未知路径：%s" % path)
        except AppError as e:
            return self._error(e.status, e.message)
        except Exception:
            traceback.print_exc()
            return self._error(500, "服务器内部错误（看控制台 traceback）")

    def do_DELETE(self):
        path, q = self._query()
        try:
            if path == "/api/quad":
                return self._json(200, self.server.app.delete_quad(
                    self._q1(q, "th"), self._q1(q, "id")))
            return self._error(404, "未知路径：%s" % path)
        except AppError as e:
            return self._error(e.status, e.message)
        except Exception:
            traceback.print_exc()
            return self._error(500, "服务器内部错误（看控制台 traceback）")

    # ---- 小工具 ----
    @staticmethod
    def _q1(q, key):
        vals = q.get(key) or [""]
        return str(vals[0]).strip()

    def _read_body(self):
        raw_len = self.headers.get("Content-Length")
        if not raw_len:
            return {}
        try:
            length = int(raw_len)
        except ValueError:
            raise AppError(400, "Content-Length 非法")
        if length <= 0:
            return {}
        if length > MAX_BODY_BYTES:
            raise AppError(413, "请求体过大（> %d 字节）" % MAX_BODY_BYTES)
        raw = self.rfile.read(length)
        try:
            # utf-8-sig：兼容 PowerShell Set-Content / 某些 curl 场景写出的 BOM
            return json.loads(raw.decode("utf-8-sig"))
        except (ValueError, UnicodeError):
            raise AppError(400, "请求体不是合法 JSON")

    def _serve_index(self):
        try:
            with open(INDEX_PATH, "rb") as f:
                data = f.read()
        except OSError:
            raise AppError(500, "找不到页面文件：%s" % INDEX_PATH)
        self._send(200, data, ctype="text/html; charset=utf-8")

    def _serve_image(self, th, bid):
        g, base = self.server.app.find_base(th, bid)
        path = base["image"]
        try:
            with open(path, "rb") as f:
                data = f.read()
        except OSError:
            raise AppError(500, "读不到底图：%s" % path)
        ctype = "image/png" if data.startswith(_PNG_SIG) else "image/jpeg"
        try:
            st = os.stat(path)
            etag = '"%x-%x"' % (st.st_mtime_ns, st.st_size)
        except OSError:
            etag = None
        if etag and self.headers.get("If-None-Match") == etag:
            # 304 不能带 body，也不要重复 Content-Length
            self.send_response(304)
            self.send_header("ETag", etag)
            self.send_header("Cache-Control", "no-cache, must-revalidate")
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache, must-revalidate")
        if etag:
            self.send_header("ETag", etag)
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass


# ---------------------------------------------------------------------------
# 启动
# ---------------------------------------------------------------------------

def parse_args(argv=None):
    ap = argparse.ArgumentParser(
        description="TH16 阵型标注工具（本地网页；预填 layout.json，点选/拖拽修正，自动保存）")
    ap.add_argument("--host", default="127.0.0.1", help="监听地址（默认 127.0.0.1，仅本机）")
    ap.add_argument("--port", type=int, default=8765, help="监听端口（默认 8765，被占用时自动 +1 试到 +20）")
    ap.add_argument("--root", default=None, help="项目根目录（含 bases/），默认按脚本位置推断")
    ap.add_argument("--no-open", action="store_true", help="启动后不自动打开浏览器")
    ap.add_argument("--strict-port", action="store_true", help="端口被占用时直接报错，不自动换端口")
    return ap.parse_args(argv)


def resolve_root(arg=None):
    root = os.path.abspath(arg) if arg else os.environ.get("ANNOTATE_ROOT") or DEFAULT_ROOT
    if not os.path.isdir(os.path.join(root, "bases")):
        raise SystemExit("找不到 bases/ 目录：%s\n用 --root 指定项目根目录（里面有 bases/）" % root)
    return root


def bind_server(app, host, port, strict=False):
    last_err = None
    for offset in range(0, 21):
        p = int(port) + offset
        try:
            return AnnotateServer((host, p), app), p
        except OSError as e:
            last_err = e
            if strict:
                break
    raise SystemExit("端口 %s 绑定失败：%s（可用 --port 换一个端口）" % (port, last_err))


def main(argv=None):
    args = parse_args(argv)
    root = resolve_root(args.root)
    app = App(root)
    groups = app.groups()
    total = sum(len(g["bases"]) for g in groups)
    srv, port = bind_server(app, args.host, args.port, args.strict_port)
    url = "http://%s:%d/" % (args.host, port)
    print("ClashLab 阵型标注工具已启动")
    print("  项目根目录: %s" % root)
    print("  发现阵型: %s" % (", ".join("%s=%d 阵" % (g["th"].upper(), len(g["bases"])) for g in groups)
                              or "（没有找到 bases/<th>/NN，检查 --root）"))
    print("  输出目录: %s" % os.path.join(root, core.OUT_DIR_REL))
    print("  地址: %s%s" % (url, "" if port == args.port else "（端口 %d 被占用，已自动换）" % args.port))
    print("  快捷键: 1-9 选类型 / Enter 保存并下一阵 / Backspace 撤销 / Space 跳过 / "
          "Q,E 切候选 / Tab 下一栋 / 方向键微调 / H 帮助")
    print("  Ctrl+C 退出")
    if not args.no_open:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n已退出")
    finally:
        srv.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
