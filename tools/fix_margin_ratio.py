# -*- coding: utf-8 -*-
import os, re
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
p = os.path.join(BASE, 'android', 'assets', 'annotate7.html')
t = open(p, encoding='utf-8').read()
t = t.replace('var MARGIN=0.18, IMG={w:0,h:0,offX:0,offY:0};', 'var MARGIN=0.15, IMG={w:0,h:0,offX:0,offY:0};', 1)
old = '''function fitCanvas(){var stg=document.getElementById('stage');var aw=stg.clientWidth,ah=stg.clientHeight;
  if(!aw||!ah||!img.naturalWidth)return;
  var inner=1-2*MARGIN;
  var r=Math.min(aw*inner/img.naturalWidth, ah*inner/img.naturalHeight);
  var iw=Math.max(1,Math.round(img.naturalWidth*r)), ih=Math.max(1,Math.round(img.naturalHeight*r));
  var cw=Math.round(iw/inner), ch=Math.round(ih/inner);
  cv.width=cw;cv.height=ch;cv.style.width=cw+'px';cv.style.height=ch+'px';
  IMG.w=iw;IMG.h=ih;IMG.offX=Math.round((cw-iw)/2);IMG.offY=Math.round((ch-ih)/2);
  return r;}'''
new = '''function fitCanvas(){var stg=document.getElementById('stage');var aw=stg.clientWidth,ah=stg.clientHeight;
  if(!aw||!ah||!img.naturalWidth)return;
  var factor=1+2*MARGIN;
  var r=Math.min(aw/(img.naturalWidth*factor), ah/(img.naturalHeight*factor));
  var iw=Math.max(1,Math.round(img.naturalWidth*r)), ih=Math.max(1,Math.round(img.naturalHeight*r));
  var cw=Math.round(iw*factor), ch=Math.round(ih*factor);
  cv.width=cw;cv.height=ch;cv.style.width=cw+'px';cv.style.height=ch+'px';
  IMG.w=iw;IMG.h=ih;IMG.offX=Math.round(iw*MARGIN);IMG.offY=Math.round(ih*MARGIN);
  return r;}'''
t = t.replace(old, new, 1)
open(p, 'w', encoding='utf-8', newline='\n').write(t)
print('margin 0.15 + fit fixed', len(t))