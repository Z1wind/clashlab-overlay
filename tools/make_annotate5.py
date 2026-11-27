# -*- coding: utf-8 -*-
"""v0.2.4 页面：类型列表默认收起为一行按钮，点开浮层选择，选完自动收起。"""
import os, shutil
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
src = os.path.join(BASE, "android", "assets", "annotate4.html")
dst = os.path.join(BASE, "android", "assets", "annotate5.html")
t = open(src, encoding="utf-8").read()

# 1) HTML：pal 结构改为 一行按钮 + 可展开面板
old_pal = '<div id="pal"><div id="cattabs"></div><div id="types"></div><button id="btnPalHide">收</button></div>'
new_pal = '''<div id="pal">
      <div id="palbar"><button id="btnPalToggle">建筑：防空 ▾</button><span id="palhint">点这里选类型</span></div>
      <div id="palsheet"><div id="cattabs"></div><div id="types"></div></div>
    </div>'''
if old_pal in t:
    t = t.replace(old_pal, new_pal, 1)
else:
    print("pal html anchor miss")

# 2) CSS：pal 悬浮改为 palbar 常驻一行 + palsheet 浮层
t = t.replace('#pal{position:absolute;left:0;right:0;bottom:0;z-index:6;background:rgba(21,27,36,.97);border-top:1px solid #263141;padding:3px 6px 4px;max-height:96px;overflow:hidden}',
'''#pal{position:absolute;left:0;right:0;bottom:0;z-index:6}
#palbar{display:flex;align-items:center;gap:6px;background:rgba(21,27,36,.97);border-top:1px solid #263141;padding:4px 8px}
#palbar button{font-size:13px;padding:6px 10px;background:#2e6b3e;border-color:#49a35f;color:#fff}
#palhint{color:#8fa3bd;font-size:11px}
#palsheet{display:none;background:rgba(21,27,36,.98);border-top:1px solid #263141;padding:4px 6px;max-height:34vh;overflow-y:auto}''')
t = t.replace('#pal .cat', '#palsheet .cat')

# 3) JS：buildPalette 更新按钮文字；选完收起；toggle 打开面板
old_bp = '''function buildPalette(){var tabs=document.getElementById('cattabs'),types=document.getElementById('types');tabs.innerHTML='';types.innerHTML='';
  CATS.forEach(function(cat,ci){var b=document.createElement('button');b.textContent=cat[0];if(ci===catIdx)b.className='on';b.onclick=function(){catIdx=ci;buildPalette();};tabs.appendChild(b);});
  CATS[catIdx][1].forEach(function(t){var b=document.createElement('button');b.textContent=(SNAME[t]||t);if(t===sel)b.className='on';b.onclick=function(){sel=t;buildPalette();toast('已选中：'+(CNAME[t]||t));};types.appendChild(b);});}'''
new_bp = '''function palOpen(open){document.getElementById('palsheet').style.display=open?'block':'none';
  document.getElementById('btnPalToggle').textContent='建筑：'+(SNAME[sel]||sel)+(open?' ▴':' ▾');}
function closeSheet(){palOpen(false);}
function buildPalette(){var tabs=document.getElementById('cattabs'),types=document.getElementById('types');tabs.innerHTML='';types.innerHTML='';
  CATS.forEach(function(cat,ci){var b=document.createElement('button');b.textContent=cat[0];if(ci===catIdx)b.className='on';b.onclick=function(){catIdx=ci;buildPalette();};tabs.appendChild(b);});
  CATS[catIdx][1].forEach(function(t){var b=document.createElement('button');b.textContent=(SNAME[t]||t);if(t===sel)b.className='on';b.onclick=function(){sel=t;catIdx=catIdx;buildPalette();palOpen(false);toast('已选中：'+(CNAME[t]||t));};types.appendChild(b);});
  document.getElementById('btnPalToggle').textContent='建筑：'+(SNAME[sel]||sel)+(document.getElementById('palsheet').style.display==='block'?' ▴':' ▾');}
document.getElementById('btnPalToggle').onclick=function(){var sh=document.getElementById('palsheet');palOpen(sh.style.display!=='block');};'''
if old_bp in t:
    t = t.replace(old_bp, new_bp, 1)
else:
    print("buildPalette anchor miss")

# 4) updateUI：标定后隐藏步骤/提示，未标定时隐藏整个 pal；标定后显示 palbar、收面板
old_ui = '''  if(s.corners.length<4)document.getElementById('hint').textContent='点四个角（已点 '+s.corners.length+'/4，黄点可拖，＋－缩放）';
  document.getElementById('pal').style.display=s.corners.length<4?'none':'block';}'''
new_ui = '''  if(s.corners.length<4)document.getElementById('hint').textContent='点四个角（已点 '+s.corners.length+'/4，黄点可拖，＋－缩放）';
  var calibrated=s.corners.length===4;
  document.getElementById('pal').style.display=calibrated?'block':'none';
  document.getElementById('steps').style.display=calibrated?'none':'flex';
  document.getElementById('hint').style.display=calibrated?'none':'block';
  if(calibrated)palOpen(document.getElementById('palsheet').style.display==='block');}'''
if old_ui in t:
    t = t.replace(old_ui, new_ui, 1)
else:
    print("updateUI anchor miss")
open(dst, "w", encoding="utf-8", newline="\n").write(t)
print("annotate5 written", len(t))
