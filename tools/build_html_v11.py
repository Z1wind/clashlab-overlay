# -*- coding: utf-8 -*-
"""生成 HTML v1.1：滚轮缩放 + 左键拖动平移 + 网格加亮 + 去掉边缘自动平移。"""
import base64, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
src = os.path.join(BASE, "android", "assets", "annotate10.html")
t = open(src, encoding="utf-8").read()
IMGDIR = os.path.join(BASE, "android", "assets", "img")
uris = []
for i in range(1, 21):
    b64 = base64.b64encode(open(os.path.join(IMGDIR, "b%02d.jpg" % i), "rb").read()).decode("ascii")
    uris.append("data:image/jpeg;base64," + b64)
old = "var IMAGES=[];for(var i=1;i<=20;i++){IMAGES.push('img/b'+(i<10?'0'+i:i)+'.jpg');}"
new = ("var IMGIDS=[];for(var i=1;i<=20;i++){IMGIDS.push('img/b'+(i<10?'0'+i:i)+'.jpg');}\n"
       "var IMAGES=" + repr(uris).replace("'", '"') + ";")
t = t.replace(old, new, 1)
t = t.replace("var doc=saveDoc(s,IMAGES[cur]);", "var doc=saveDoc(s,IMGIDS[cur]);", 1)
t = t.replace("docs.push(saveDoc(s,IMAGES[i]));", "docs.push(saveDoc(s,IMGIDS[i]));", 1)
# 1) 网格加亮
t = t.replace("ctx.strokeStyle='rgba(80,200,255,.30)';ctx.lineWidth=1;",
              "ctx.strokeStyle='rgba(0,240,255,.60)';ctx.lineWidth=1.3;", 1)
# 2) 任意缩放级别都允许拖动平移
t = t.replace("if(view.scale>1.01){tapStart.pan=true;}", "tapStart.pan=true;", 1)
# 3) HTML 版关闭边缘自动平移
t = t.replace("var EDGE=36,STEP=2,moved=false;", "var EDGE=0,STEP=0,moved=false;", 1)
# 4) 滚轮缩放（以指针为中心）
wheel = ("cv.addEventListener('wheel',function(ev){ev.preventDefault();"
         "var r=cv.getBoundingClientRect();"
         "var sx=(ev.clientX-r.left)*(cv.width/r.width),sy=(ev.clientY-r.top)*(cv.height/r.height);"
         "var cx=(sx-view.panX)/view.scale,cy=(sy-view.panY)/view.scale;"
         "var f=ev.deltaY<0?1.15:1/1.15;var ns=Math.max(0.2,Math.min(8,view.scale*f));"
         "view.panX=sx-cx*ns;view.panY=sy-cy*ns;view.scale=ns;draw();},{passive:false});\n")
t = t.replace("cv.addEventListener('mousedown',onDown);", wheel + "cv.addEventListener('mousedown',onDown);", 1)
# 5) 缩小按钮允许 <1
t = t.replace("view.scale=Math.max(1,view.scale/1.35);if(view.scale===1){view.panX=0;view.panY=0;}",
              "view.scale=Math.max(0.2,view.scale/1.35);", 1)
# 6) 帮助与标题
t = t.replace("<h3>30 秒上手（v0.3.0）</h3>", "<h3>30 秒上手（HTML v1.1）</h3>")
t = t.replace("黄点出现后<b>按住可拖动</b>到真正的角，可拖到图片外面；拖到屏幕边缘会<b>自动平移</b>。",
              "黄点出现后<b>按住可拖动</b>到真正的角，可拖到图片外面。<b>滚轮缩放、左键拖动平移画面</b>。")
t = t.replace("图片太小：<b>双击图面 2x 放大</b>，或用右上 <b>＋ / － / 适应</b>，也可双指捏合。",
              "图片太小：<b>滚轮缩放</b>，或右上 <b>＋ / － / 适应</b>；<b>左键拖动</b>可平移画面。")
t = t.replace("「导出全部」保存 JSON（Android 10+ 在「下载」）。首次权限请点允许。",
              "「导出全部」保存 JSON 到浏览器下载目录；进度自动存在本机浏览器。")
t = t.replace("<title>阵型标注</title>", "<title>ClashLab 阵型标注（HTML 版）</title>")
out = os.path.join(BASE, "dist", "ClashLabAnnotator_HTML_v1.1.html")
open(out, "w", encoding="utf-8", newline="\n").write(t)
print("wrote", out, os.path.getsize(out))
