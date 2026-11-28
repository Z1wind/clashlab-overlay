# -*- coding: utf-8 -*-
"""桌面 app 升级：内置 ONNX 预标注 API（v1.3）。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "desktop_app.py")
t = open(p, encoding="utf-8").read()
t = t.replace('APP_TITLE = "ClashLab 阵型标注（桌面版 v1.2）"', 'APP_TITLE = "ClashLab 阵型标注（桌面版 v1.3）"')
t = t.replace('html = resource_path("ClashLabAnnotator_HTML_desktop.html")',
              'html = resource_path("ClashLabAnnotator_Desktop_v3.html")')
t = t.replace('html = resource_path("ClashLabAnnotator_Desktop_v2.html")',
              'html = resource_path("ClashLabAnnotator_Desktop_v3.html")')
# 追加预标注实现
extra = '''

_ANNOTATOR = None
IMG_DIR = None

def get_annotator():
    global _ANNOTATOR
    if _ANNOTATOR is None:
        from tools.preannotate_core import PreAnnotator
        _ANNOTATOR = PreAnnotator(
            resource_path(os.path.join("models", "pipeline_gate.onnx")),
            resource_path(os.path.join("models", "pipeline_type.onnx")),
            resource_path(os.path.join("models", "pipeline_types.json")),
        )
    return _ANNOTATOR

def get_img_dir():
    global IMG_DIR
    if IMG_DIR is None:
        IMG_DIR = resource_path("img")
    return IMG_DIR
'''
if "def get_annotator()" not in t:
    t = t.replace("class Api:", extra.strip() + "\n\nclass Api:", 1)
# 在 Api 里加方法
method = '''
    def preannotate(self, corners_norm, image_size, image_rel):
        import time
        try:
            import cv2, numpy as np
            from clashlab.assets import STATS
            img_path = os.path.join(get_img_dir(), os.path.basename(str(image_rel)))
            img = cv2.imdecode(np.fromfile(img_path, np.uint8), cv2.IMREAD_COLOR)
            if img is None:
                return {"ok": False, "error": "image not found: " + img_path}
            wn, hn = float(image_size[0]), float(image_size[1])
            quad = [[float(u) * wn, float(v) * hn] for u, v in corners_norm]
            t0 = time.time()
            out = get_annotator().detect(img, quad)
            ms = int((time.time() - t0) * 1000)
            buildings = []
            for o in out:
                size = int((STATS.get(o["type"]) or {}).get("size") or 2)
                cx, cy = o["center"]
                tx = int(round(cx - size / 2.0))
                ty = int(round(cy - size / 2.0))
                if tx < 0 or ty < 0 or tx > 43 or ty > 43:
                    continue
                buildings.append({"type": o["type"], "tile": [tx, ty]})
            return {"ok": True, "buildings": buildings, "ms": ms}
        except Exception as e:
            return {"ok": False, "error": str(e)}
'''
if "def preannotate(self" not in t:
    t = t.replace("    def open_export_dir(self):", method + "\n    def open_export_dir(self):", 1)
# smoke 模式 2：直接测预标注
smoke2 = '''
    if smoke == 2:
        def on_loaded2():
            try:
                import json
                r = api.preannotate([[0.106,0.51],[0.491,-0.104],[0.875,0.508],[0.489,1.133]],
                                    [1600, 735], "img/b03.jpg")
                res = {"ok": r.get("ok"), "n": len(r.get("buildings") or []), "ms": r.get("ms"), "error": r.get("error")}
                with open(os.path.join(os.path.dirname(sys.executable if getattr(sys, "frozen", False) else __file__), "smoke2_result.json"), "w", encoding="utf-8") as f:
                    json.dump(res, f, ensure_ascii=False)
                print("SMOKE2", res, flush=True)
            finally:
                win.destroy()
        win.events.loaded += on_loaded2
'''
t = t.replace('    smoke = os.environ.get("CLASHLAB_SMOKE") == "1"',
              '    smoke_env = os.environ.get("CLASHLAB_SMOKE", "")\n    smoke = int(smoke_env) if smoke_env.isdigit() else (1 if smoke_env == "1" else 0)\n    smoke = 1 if smoke == 1 else (2 if smoke == 2 else 0)', 1)
if "smoke2_result.json" not in t:
    t = t.replace('    webview.start(debug=False)', smoke2 + '\n    webview.start(debug=False)', 1)
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("desktop_app v1.3 patched", len(t))
