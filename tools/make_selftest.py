# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
src = os.path.join(BASE, 'android', 'assets', 'annotate7.html')
t = open(src, encoding='utf-8').read()
hook = '''
setTimeout(function(){
  try{
    var s=S(); s.corners=[]; s.buildings=[];
    doTap(IMG.offX+IMG.w*0.25, IMG.offY+IMG.h*0.25);
    doTap(IMG.offX+IMG.w*0.85, IMG.offY+IMG.h*0.25);
    doTap(IMG.offX+IMG.w*0.85, IMG.offY+IMG.h*0.85);
    doTap(IMG.offX+IMG.w*0.25, IMG.offY+IMG.h*0.85);
    var before=JSON.stringify(s.corners[0]);
    s.corners.pop();
    doTap(IMG.offX-IMG.w*0.20, IMG.offY+IMG.h*0.5);
    var outside=s.corners[s.corners.length-1];
    draw();
    document.getElementById('tip').textContent='SELFTEST off='+IMG.offX+','+IMG.offY+' wh='+IMG.w+'x'+IMG.h
      +' first='+before+' outside='+JSON.stringify(outside)
      +' ok_outside='+(outside[0] < -0.05);
  }catch(e){ document.getElementById('tip').textContent='SELFTEST ERR '+e; }
}, 1200);
'''
t = t.replace('</script></body></html>', hook + '\n</script></body></html>')
out = os.path.join(BASE, 'out', 'apk_qa', 'annotate7_selftest.html')
open(out, 'w', encoding='utf-8', newline='\n').write(t)
print('selftest written', out)