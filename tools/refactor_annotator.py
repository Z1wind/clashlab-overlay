# -*- coding: utf-8 -*-
"""把 tools/annotate_web.py 重构为可内置的 clashlab/annotator.py（服务 + 幂等启动）。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
src = open(os.path.join(BASE, "tools", "annotate_web.py"), encoding="utf-8").read()
cut = src.index("def main():")
head = src[:cut]
# 模块文档替换
head = head.replace('"""本地网页标注器：战争截图 -> 点 4 角标定 -> 点建筑选类型 -> 导出 annotated JSON。',
                    '"""内置网页标注器服务（可被覆盖层面板直接拉起）。\n\n用法：\n    from clashlab import annotator\n    annotator.start_server(root)      # 幂等；已在跑则直接返回\n浏览器打开 http://127.0.0.1:8765 。\n\n原始说明：战争截图 -> 点 4 角标定 -> 点建筑选类型 -> 导出 annotated JSON。')
tail = '''

_HTTPD = None
_PORT = None


def is_running(port=8765, timeout=0.4):
    """探测本地标注器是否已响应。"""
    import socket
    try:
        with socket.create_connection(("127.0.0.1", int(port)), timeout=timeout):
            return True
    except OSError:
        return False


def _default_image(root):
    """未指定图片时，挑一张最近的真实战图。"""
    cands = [os.path.join(root, "out", "live", n) for n in
             ("enemy_scout_live.png", "war_scout_shadow_th17.png", "panel_now.png")]
    for c in cands:
        if os.path.exists(c):
            return c
    live = os.path.join(root, "out", "live")
    if os.path.isdir(live):
        pngs = [os.path.join(live, f) for f in os.listdir(live) if f.lower().endswith(".png")]
        if pngs:
            return max(pngs, key=os.path.getmtime)
    return None


def start_server(root, image=None, out_dir=None, port=8765):
    """幂等启动：已在跑则返回 None；否则启动后台线程并返回 httpd。"""
    global _HTTPD, _PORT
    if is_running(port):
        return None
    if _HTTPD is not None:
        try:
            _HTTPD.shutdown()
        except Exception:
            pass
        _HTTPD = None
    img = image or _default_image(root)
    if not img or not os.path.exists(img):
        raise FileNotFoundError("没有找到可标注的图片（out/live/*.png）")
    _HTTPD = serve(img, out_dir, port)
    _PORT = port
    return _HTTPD


def open_page(port=8765):
    import webbrowser
    url = "http://127.0.0.1:%d/" % int(port)
    webbrowser.open(url)
    return url


def ensure_running(root, port=8765, open_browser=True):
    """面板按钮用：保证服务在跑，并打开页面。返回 (url, started)。"""
    started = start_server(root, port=port) is not None
    url = open_page(port) if open_browser else "http://127.0.0.1:%d/" % int(port)
    return url, started


def stop_server():
    global _HTTPD
    if _HTTPD is not None:
        try:
            _HTTPD.shutdown()
        except Exception:
            pass
        _HTTPD = None


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--image", default=None)
    ap.add_argument("--port", type=int, default=8765)
    a = ap.parse_args()
    h = start_server(a.root, image=a.image, port=a.port)
    print("annotator:", open_page(a.port), "(started=%s)" % bool(h))
'''
open(os.path.join(BASE, "clashlab", "annotator.py"), "w", encoding="utf-8", newline="\n").write(head + tail)
print("clashlab/annotator.py written", len(head + tail))

# tools/annotate_web.py 变薄 CLI（保持向后兼容）
thin = '''# -*- coding: utf-8 -*-
"""兼容入口：转发到 clashlab.annotator（真正逻辑已内置，可被覆盖层直接调用）。"""
import argparse, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from clashlab import annotator


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", default=None)
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args()
    h = annotator.start_server(ROOT, image=a.image, out_dir=a.out_dir, port=a.port)
    print("annotator: http://127.0.0.1:%d (started=%s)" % (a.port, bool(h)))
    if not a.no_browser:
        annotator.open_page(a.port)
    print("Ctrl+C 退出")
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        annotator.stop_server()


if __name__ == "__main__":
    main()
'''
open(os.path.join(BASE, "tools", "annotate_web.py"), "w", encoding="utf-8", newline="\n").write(thin)
print("tools/annotate_web.py thinned")
