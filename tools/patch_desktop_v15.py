# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "desktop_app.py")
t = open(p, encoding="utf-8").read()
t = t.replace('APP_TITLE = "ClashLab 阵型标注（桌面版 v1.3）"', 'APP_TITLE = "ClashLab 阵型标注（桌面版 v1.5）"')
t = t.replace('html = resource_path("ClashLabAnnotator_Desktop_v3.html")', 'html = resource_path("ClashLabAnnotator_Desktop_v3.html")')
old = '''def get_annotator():
    global _ANNOTATOR
    if _ANNOTATOR is None:
        from tools.preannotate_core import PreAnnotator
        _ANNOTATOR = PreAnnotator(
            resource_path(os.path.join("models", "pipeline_gate.onnx")),
            resource_path(os.path.join("models", "pipeline_type.onnx")),
            resource_path(os.path.join("models", "pipeline_types.json")),
        )
    return _ANNOTATOR'''
new = '''def get_annotator():
    global _ANNOTATOR
    if _ANNOTATOR is None:
        from tools.preannotate_core import HybridAnnotator
        _ANNOTATOR = HybridAnnotator(
            resource_path(os.path.join("models", "hybrid_gate.onnx")),
            resource_path(os.path.join("models", "hybrid_emb.onnx")),
            resource_path(os.path.join("models", "hybrid_protos.npz")),
            resource_path(os.path.join("models", "hybrid_meta.json")),
        )
    return _ANNOTATOR'''
if old in t:
    t = t.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("desktop_app -> HybridAnnotator v1.5")
else:
    print("anchor miss")
