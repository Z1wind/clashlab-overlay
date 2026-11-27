# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
p = os.path.join(BASE, 'android', 'assets', 'annotate7.html')
t = open(p, encoding='utf-8').read()
t = t.replace('var MARGIN=0.15, IMG={w:0,h:0,offX:0,offY:0};', 'var MARGIN=0.06, IMG={w:0,h:0,offX:0,offY:0};', 1)
old = '''function fitCanvas(){var stg=document.getElementById('stage');var aw=stg.clientWidth,ah=stg.clientHeight;
  if(!aw||!ah||!img.naturalWidth)return;
  var factor=1+2*MARGIN;
  var r=Math.min(aw/(img.naturalWidth*factor), ah/(img.naturalHeight*factor));
  var iw=Math.max(1,Math.round(img.naturalWidth*r)), ih=Math.max(1,Math.round(img.naturalHeight*r));
  var cw=Math.round(iw*factor), ch=Math.round(ih*factor);
  cv.width=cw;cv.height=ch;cv.style.width=cw+'px';cv.style.height=ch+'px';
  IMG.w=iw;IMG.h=ih;IMG.offX=Math.round(iw*MARGIN);IMG.offY=Math.round(ih*MARGIN);
  return r;}'''
new = '''function fitCanvas(){var stg=document.getElementById('stage');var aw=stg.clientWidth,ah=stg.clientHeight;
  if(!aw||!ah||!img.naturalWidth)return;
  var r=Math.min(aw*(1-2*MARGIN)/img.naturalWidth, ah*(1-2*MARGIN)/img.naturalHeight);
  var iw=Math.max(1,Math.round(img.naturalWidth*r)), ih=Math.max(1,Math.round(img.naturalHeight*r));
  cv.width=aw;cv.height=ah;cv.style.width=aw+'px';cv.style.height=ah+'px';
  IMG.w=iw;IMG.h=ih;IMG.offX=Math.round((aw-iw)/2);IMG.offY=Math.round((ah-ih)/2);
  return r;}'''
t = t.replace(old, new, 1)
open(p, 'w', encoding='utf-8', newline='\n').write(t)
print('stage-relative margin 0.06', len(t))