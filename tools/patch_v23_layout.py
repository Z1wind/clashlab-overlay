# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "android", "assets", "annotate4.html")
t = open(p, encoding="utf-8").read()
# 1) 列表改为悬浮层：移到 #stage 内，绝对定位
t = t.replace('<div id="stage"><canvas id="cv"></canvas><div id="tip">第 1/20 张</div>\n    <div id="zoom"><button id="btnZoomOut">－</button><button id="btnZoomFit">适应</button><button id="btnZoomIn">＋</button></div>\n  </div>\n  <div id="pal"><div id="cattabs"></div><div id="types"></div></div>',
'<div id="stage"><canvas id="cv"></canvas><div id="tip">第 1/20 张</div>\n    <div id="zoom"><button id="btnZoomOut">－</button><button id="btnZoomFit">适应</button><button id="btnZoomIn">＋</button></div>\n    <div id="pal"><div id="cattabs"></div><div id="types"></div><button id="btnPalHide">收</button></div>\n  </div>')
# 2) CSS 调整
t = t.replace('#pal{background:#151b24;border-top:1px solid #263141;padding:3px 6px}',
'#pal{position:absolute;left:0;right:0;bottom:0;z-index:6;background:rgba(21,27,36,.97);border-top:1px solid #263141;padding:3px 6px 4px;max-height:96px;overflow:hidden}')
t = t.replace('#zoom{position:absolute;right:6px;bottom:6px;display:flex;gap:4px}',
'#zoom{position:absolute;right:6px;top:6px;display:flex;gap:4px;z-index:7}')
t = t.replace('#stage{position:relative;flex:1;overflow:hidden;background:#000;display:flex;align-items:center;justify-content:center;min-height:44vh}',
'#stage{position:relative;flex:1;overflow:hidden;background:#000;display:flex;align-items:center;justify-content:center;min-height:0}')
# 3) 收起列表按钮 + 逻辑
t = t.replace('document.getElementById("btnZoomFit").onclick=function(){view={scale:1,panX:0,panY:0};draw();toast("已适应屏幕");};',
'''document.getElementById('btnZoomFit').onclick=function(){view={scale:1,panX:0,panY:0};draw();toast('已适应屏幕');};
var palHidden=false;
document.getElementById('btnPalHide').onclick=function(){palHidden=!palHidden;var pal=document.getElementById('pal');
  pal.querySelector('#cattabs').style.display=palHidden?'none':'flex';
  pal.querySelector('#types').style.display=palHidden?'none':'flex';
  this.textContent=palHidden?'展开':'收';};''')
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("layout patched", len(t))
