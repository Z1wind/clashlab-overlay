# -*- coding: utf-8 -*-
import hashlib, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
p = os.path.join(BASE, 'docs', 'APK_20BASES.md')
t = open(p, encoding='utf-8').read()
t = t.replace('- APK 8,300,644 bytes；页面脚本 node --check 通过',
              '- APK 8,300,644 bytes md5 ' + hashlib.md5(open(os.path.join(BASE,'dist','ClashLabAnnotator_20bases_v0.2.6.apk'),'rb').read()).hexdigest().upper() + '；页面脚本 node --check 通过')
t = t.replace('- 画布四周留出 18% 边距，图片居中显示', '- 画布四周留出 15% 边距（图片约占屏幕 77%），角点可拖到图片外')
t = t.replace('- 无头浏览器自测：off=255,117 / 图片 906x416 / 角点 outside=[-0.2,0.5] / ok=true',
              '- 无头浏览器自测：off=163,75 / 图片 1088x500 / 角点 outside=[-0.2,0.5] / ok=true')
open(p, 'w', encoding='utf-8', newline='\n').write(t)
print('doc updated')