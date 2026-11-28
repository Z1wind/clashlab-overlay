# -*- coding: utf-8 -*-
"""桌面版标注器：原生窗口（WebView2），直接保存 JSON 到导出目录。"""
import json, os, sys
import webview

APP_TITLE = "ClashLab 阵型标注（桌面版 v1.5）"
EXPORT_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "ClashLab标注")

def resource_path(rel):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, rel)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dist", rel)

_ANNOTATOR = None
IMG_DIR = None

def get_annotator():
    global _ANNOTATOR
    if _ANNOTATOR is None:
        from tools.preannotate_core import HybridAnnotator
        _ANNOTATOR = HybridAnnotator(
            resource_path(os.path.join("models", "hybrid_gate.onnx")),
            resource_path(os.path.join("models", "hybrid_emb.onnx")),
            resource_path(os.path.join("models", "hybrid_protos.npz")),
            resource_path(os.path.join("models", "hybrid_meta.json")),
        )
    return _ANNOTATOR

def get_img_dir():
    global IMG_DIR
    if IMG_DIR is None:
        IMG_DIR = resource_path("img")
    return IMG_DIR

class Api:
    def save_json(self, name, content):
        try:
            os.makedirs(EXPORT_DIR, exist_ok=True)
            base = os.path.splitext(os.path.basename(name or "annot.json"))[0] or "annot"
            path = os.path.join(EXPORT_DIR, base + ".json")
            i = 2
            while os.path.exists(path):
                path = os.path.join(EXPORT_DIR, "%s_%d.json" % (base, i)); i += 1
            with open(path, "w", encoding="utf-8") as f:
                f.write(content or "")
            return {"ok": True, "path": path}
        except Exception as e:
            return {"ok": False, "error": str(e)}


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

    def open_export_dir(self):
        try:
            os.makedirs(EXPORT_DIR, exist_ok=True)
            os.startfile(EXPORT_DIR)
            return {"ok": True, "path": EXPORT_DIR}
        except Exception as e:
            return {"ok": False, "error": str(e)}

def main():
    html = resource_path("ClashLabAnnotator_Desktop_v3.html")
    if not os.path.exists(html):
        html = resource_path("ClashLabAnnotator_HTML_v1.1.html")
    api = Api()
    win = webview.create_window(APP_TITLE, url=html, js_api=api,
                                width=1660, height=980, min_size=(1100, 650),
                                text_select=True)
    smoke_env = os.environ.get("CLASHLAB_SMOKE", "")
    smoke = int(smoke_env) if smoke_env.isdigit() else (1 if smoke_env == "1" else 0)
    smoke = 1 if smoke == 1 else (2 if smoke == 2 else 0)
    if smoke == 1:
        def on_loaded():
            try:
                title = win.evaluate_js("document.title")
                imgs = win.evaluate_js("(window.IMGIDS||[]).length")
                win.evaluate_js("document.getElementById('tip').textContent")
                r = api.save_json("smoke_test.json", json.dumps({"ok": True, "title": title, "images": imgs}, ensure_ascii=False))
                with open(os.path.join(os.path.dirname(sys.executable if getattr(sys, "frozen", False) else __file__), "smoke_result.json"), "w", encoding="utf-8") as f:
                    json.dump({"title": title, "images": imgs, "save": r}, f, ensure_ascii=False)
                print("SMOKE_OK", title, imgs, r, flush=True)
            finally:
                win.destroy()
        win.events.loaded += on_loaded

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

    webview.start(debug=False)

if __name__ == "__main__":
    main()
