# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
src = os.path.join(BASE, 'android', 'assets', 'annotate6.html')
dst = os.path.join(BASE, 'android', 'assets', 'annotate7.html')
t = open(src, encoding='utf-8').read()
# 1) 边距状态
t = t.replace('var view={scale:1,panX:0,panY:0},dragIdx=-1,pinch=null;',
 'var view={scale:1,panX:0,panY:0},dragIdx=-1,pinch=null;\nvar MARGIN=0.18, IMG={w:0,h:0,offX:0,offY:0};', 1)
# 2) fitCanvas
old_fit = '''function fitCanvas(){var stg=document.getElementById('stage');var aw=stg.clientWidth,ah=stg.clientHeight;
  if(!aw||!ah||!img.naturalWidth)return;
  var r=Math.min(aw/img.naturalWidth,ah/img.naturalHeight);
  var cw=Math.max(1,Math.round(img.naturalWidth*r)),ch=Math.max(1,Math.round(img.naturalHeight*r));
  cv.width=cw;cv.height=ch;cv.style.width=cw+'px';cv.style.height=ch+'px';
  return r;}'''
new_fit = '''function fitCanvas(){var stg=document.getElementById('stage');var aw=stg.clientWidth,ah=stg.clientHeight;
  if(!aw||!ah||!img.naturalWidth)return;
  var inner=1-2*MARGIN;
  var r=Math.min(aw*inner/img.naturalWidth, ah*inner/img.naturalHeight);
  var iw=Math.max(1,Math.round(img.naturalWidth*r)), ih=Math.max(1,Math.round(img.naturalHeight*r));
  var cw=Math.round(iw/inner), ch=Math.round(ih/inner);
  cv.width=cw;cv.height=ch;cv.style.width=cw+'px';cv.style.height=ch+'px';
  IMG.w=iw;IMG.h=ih;IMG.offX=Math.round((cw-iw)/2);IMG.offY=Math.round((ch-ih)/2);
  return r;}'''
t = t.replace(old_fit, new_fit, 1)
# 3) imgToPx / bil
t = t.replace('function imgToPx(u,v){return [u*cv.width,v*cv.height];}',
 'function imgToPx(u,v){return [IMG.offX+u*IMG.w, IMG.offY+v*IMG.h];}', 1)
old_bil = 'function bil(u,v){var s=S();if(s.corners.length<4)return[u*cv.width,v*cv.height];'
new_bil = 'function bil(u,v){var s=S();if(s.corners.length<4)return imgToPx(u,v);'
t = t.replace(old_bil, new_bil, 1)
# 4) invBilinear px 基准
t = t.replace('e0=iu*cv.width-ix;e1=iv*cv.height-iy;', 'e0=(IMG.offX+iu*IMG.w)-ix;e1=(IMG.offY+iv*IMG.h)-iy;', 1)
# 5) 画图时图片按边距绘制
t = t.replace('ctx.drawImage(img,0,0,cv.width,cv.height);', 'ctx.drawImage(img,IMG.offX,IMG.offY,IMG.w,IMG.h);', 1)
# 6) nearestCorner 用 imgToPx
t = t.replace('d=Math.hypot(s.corners[i][0]*cv.width-ix,s.corners[i][1]*cv.height-iy);', 'var cp2=imgToPx(s.corners[i][0],s.corners[i][1]);d=Math.hypot(cp2[0]-ix,cp2[1]-iy);', 1)
# 7) 拖动/点角：允许超出图片（-0.25..1.25）
old_drag = 's.corners[dragIdx]=[Math.max(0,Math.min(1,p[0]/cv.width)),Math.max(0,Math.min(1,p[1]/cv.height))];'
new_drag = 's.corners[dragIdx]=[Math.max(-0.25,Math.min(1.25,(p[0]-IMG.offX)/IMG.w)),Math.max(-0.25,Math.min(1.25,(p[1]-IMG.offY)/IMG.h))];'
t = t.replace(old_drag, new_drag, 1)
old_push = 's.corners.push([Math.max(0,Math.min(1,ix/cv.width)),Math.max(0,Math.min(1,iy/cv.height))]);'
new_push = 's.corners.push([Math.max(-0.25,Math.min(1.25,(ix-IMG.offX)/IMG.w)),Math.max(-0.25,Math.min(1.25,(iy-IMG.offY)/IMG.h))]);'
t = t.replace(old_push, new_push, 1)
# 8) 帮助文案
t = t.replace('<h3>30 秒上手（v0.2.5）</h3>', '<h3>30 秒上手（v0.2.6）</h3>')
t = t.replace('黄点出现后<b>按住可拖动</b>到真正的角。', '黄点出现后<b>按住可拖动</b>到真正的角，<b>可以拖到图片外面</b>（截图被裁掉边缘时用）。')
open(dst, 'w', encoding='utf-8', newline='\n').write(t)
print('annotate7 written', len(t))