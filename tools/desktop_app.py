# -*- coding: utf-8 -*-
"""桌面版标注器：原生窗口（WebView2），直接保存 JSON 到导出目录。"""
import json, os, sys
import webview

APP_TITLE = "ClashLab 阵型标注（桌面版 v1.2）"
EXPORT_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "ClashLab标注")

def resource_path(rel):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, rel)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dist", rel)

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

    def open_export_dir(self):
        try:
            os.makedirs(EXPORT_DIR, exist_ok=True)
            os.startfile(EXPORT_DIR)
            return {"ok": True, "path": EXPORT_DIR}
        except Exception as e:
            return {"ok": False, "error": str(e)}

def main():
    html = resource_path("ClashLabAnnotator_Desktop_v2.html")
    if not os.path.exists(html):
        html = resource_path("ClashLabAnnotator_HTML_v1.1.html")
    api = Api()
    win = webview.create_window(APP_TITLE, url=html, js_api=api,
                                width=1660, height=980, min_size=(1100, 650),
                                text_select=True)
    smoke = os.environ.get("CLASHLAB_SMOKE") == "1"
    if smoke:
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
    webview.start(debug=False)

if __name__ == "__main__":
    main()
