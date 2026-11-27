# -*- coding: utf-8 -*-
"""v0.2.5：沿用上一张四角 + 双击缩放 + 全清空按钮。"""
import os, shutil
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
src = os.path.join(BASE, "android", "assets", "annotate5.html")
dst = os.path.join(BASE, "android", "assets", "annotate6.html")
t = open(src, encoding="utf-8").read()

# 1) 顶部栏加「沿上张四角」
t = t.replace('<span class="sp"></span><button id="btnPrev">上一张</button><button id="btnNext">下一张</button>',
              '<span class="sp"></span><button id="btnCopyCorners" class="sec">沿上张四角</button><button id="btnPrev">上一张</button><button id="btnNext">下一张</button>')
# 2) 底部栏加「全部清空」
t = t.replace('<button id="btnClear" class="warn">清空</button>',
              '<button id="btnClear" class="warn">清空</button><button id="btnClearAll" class="warn">全清空</button>')
# 3) 逻辑：沿用四角、全清空、双击缩放
anchor = "document.getElementById('btnExport').onclick=exportOne;"
add = '''document.getElementById('btnCopyCorners').onclick=function(){
  for(var j=cur-1;j>=0;j--){ var s=state[j]; if(s&&s.corners&&s.corners.length===4){
    var ns=S(); ns.corners=s.corners.map(function(p){return [p[0],p[1]];});
    draw(); updateUI(); saveLocal(); toast('已沿用第 '+(j+1)+' 张的四角'); return; } }
  toast('前面没有已标定的图');
};
var allArm=false,allTimer=null;
document.getElementById('btnClearAll').onclick=function(){var btn=this;
  if(!allArm){allArm=true;btn.textContent='再点全清';clearTimeout(allTimer);allTimer=setTimeout(function(){allArm=false;btn.textContent='全清空';},6000);return;}
  allArm=false;clearTimeout(allTimer);btn.textContent='全清空';state={};draw();updateUI();saveLocal();toast('已清空全部进度');};
var lastTap=0,lastTapX=0,lastTapY=0;
function maybeDoubleTap(px,py){var now=Date.now();
  if(now-lastTap<320&&Math.abs(px-lastTapX)<40&&Math.abs(py-lastTapY)<40){lastTap=0;
    if(view.scale>1.2){view={scale:1,panX:0,panY:0};toast('已还原');}else{view.scale=2;view.panX=-px*0.5;view.panY=-py*0.5;toast('双击放大 x2');}
    draw();return true;}
  lastTap=now;lastTapX=px;lastTapY=py;return false;}
'''
t = t.replace(anchor, add + anchor, 1)
# 在 onUp 的 doTap 前插入双击检测
t = t.replace('  if(tapStart&&!tapStart.moved&&!tapStart.pan){doTap(tapStart.x,tapStart.y);}',
              '  if(tapStart&&!tapStart.moved&&!tapStart.pan){var r=cv.getBoundingClientRect();if(!maybeDoubleTap(tapStart.x,tapStart.y))doTap(tapStart.x,tapStart.y);}')
open(dst, "w", encoding="utf-8", newline="\n").write(t)
print("annotate6 written", len(t))
