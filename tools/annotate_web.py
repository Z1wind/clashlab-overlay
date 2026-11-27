# -*- coding: utf-8 -*-
"""兼容入口：转发到 clashlab.annotator（真正逻辑已内置，可被覆盖层直接调用）。"""
import argparse, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from clashlab import annotator

serve = annotator.serve  # 向后兼容旧测试/脚本
STATE = annotator.STATE


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
