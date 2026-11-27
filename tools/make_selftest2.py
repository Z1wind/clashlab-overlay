# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
src = os.path.join(BASE, 'android', 'assets', 'annotate7.html')
t = open(src, encoding='utf-8').read()
hook = '''
setTimeout(function(){
  try{
    document.getElementById('help').style.display='none';
    var s=S(); s.corners=[]; s.buildings=[];
    doTap(IMG.offX+IMG.w*0.25, IMG.offY+IMG.h*0.25);
    doTap(IMG.offX+IMG.w*0.85, IMG.offY+IMG.h*0.25);
    doTap(IMG.offX+IMG.w*0.85, IMG.offY+IMG.h*0.85);
    doTap(IMG.offX+IMG.w*0.25, IMG.offY+IMG.h*0.85);
    var before=JSON.stringify(s.corners[0]);
    s.corners.pop();
    doTap(IMG.offX-IMG.w*0.20, IMG.offY+IMG.h*0.5);
    var outside=s.corners[s.corners.length-1];
    draw(); updateUI();
    document.getElementById('tip').textContent='SELFTEST off='+IMG.offX+','+IMG.offY+' wh='+IMG.w+'x'+IMG.h
      +' outside='+JSON.stringify(outside)+' ok='+(outside[0] < -0.05);
  }catch(e){ document.getElementById('tip').textContent='SELFTEST ERR '+e; }
}, 2000);
'''
t = t.replace('</script></body></html>', hook + '\n</script></body></html>')
for p in (os.path.join(BASE, 'out', 'apk_qa', 'annotate7_selftest.html'),
          os.path.join(BASE, 'android', 'assets', 'annotate7_selftest.html')):
    open(p, 'w', encoding='utf-8', newline='\n').write(t)
print('selftest v2 written')