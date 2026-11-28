# -*- coding: utf-8 -*-
"""生成单文件 HTML 标注器：内嵌 20 张图（base64），功能对齐 APK v0.3.0。"""
import base64, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
src = os.path.join(BASE, "android", "assets", "annotate10.html")
t = open(src, encoding="utf-8").read()
IMGDIR = os.path.join(BASE, "android", "assets", "img")
uris = []
for i in range(1, 21):
    name = "b%02d.jpg" % i
    p = os.path.join(IMGDIR, name)
    b64 = base64.b64encode(open(p, "rb").read()).decode("ascii")
    uris.append("data:image/jpeg;base64," + b64)
print("embedded", len(uris), "images, total b64 MB", round(sum(len(u) for u in uris) / 1048576.0, 2))
old = "var IMAGES=[];for(var i=1;i<=20;i++){IMAGES.push('img/b'+(i<10?'0'+i:i)+'.jpg');}"
new = ("var IMGIDS=[];for(var i=1;i<=20;i++){IMGIDS.push('img/b'+(i<10?'0'+i:i)+'.jpg');}\n"
       "var IMAGES=" + repr(uris).replace("'", '"') + ";")
if old in t:
    t = t.replace(old, new, 1); print("IMAGES replaced")
else:
    print("IMAGES anchor miss")
# 导出时用 IMGIDS 而不是 data URI
t = t.replace("var doc=saveDoc(s,IMAGES[cur]);", "var doc=saveDoc(s,IMGIDS[cur]);", 1)
t = t.replace("docs.push(saveDoc(s,IMAGES[i]));", "docs.push(saveDoc(s,IMGIDS[i]));", 1)
# 帮助文案
t = t.replace("<h3>30 秒上手（v0.3.0）</h3>", "<h3>30 秒上手（HTML v1.0）</h3>")
t = t.replace("「导出全部」保存 JSON（Android 10+ 在「下载」）。首次权限请点允许。",
              "「导出全部」保存 JSON 到浏览器下载目录；进度自动存在本机浏览器。")
t = t.replace("<title>阵型标注</title>", "<title>ClashLab 阵型标注（HTML 版）</title>")
out = os.path.join(BASE, "dist", "ClashLabAnnotator_HTML_v1.0.html")
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, "w", encoding="utf-8", newline="\n").write(t)
print("wrote", out, os.path.getsize(out), "bytes")
