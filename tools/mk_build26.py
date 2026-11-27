# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
p = os.path.join(BASE, 'android', 'java', 'com', 'clashlab', 'annotator', 'MainActivity.java')
t = open(p, encoding='utf-8').read()
t = t.replace('web.loadUrl("file:///android_asset/annotate6.html");', 'web.loadUrl("file:///android_asset/annotate7.html");')
open(p, 'w', encoding='utf-8', newline='\n').write(t)
print('activity -> annotate7')
src = os.path.join(BASE, 'tools', 'build_apk25.py')
b = open(src, encoding='utf-8').read()
b = (b.replace('classes25','classes26').replace('dex25','dex26').replace('base25','base26').replace('aligned25','aligned26')
      .replace('"--version-code", "7"','"--version-code", "8"').replace('"--version-name", "0.2.5"','"--version-name", "0.2.6"')
      .replace('ClashLabAnnotator_v25.apk','ClashLabAnnotator_v26.apk').replace('构建 APK v0.2.5','构建 APK v0.2.6'))
open(os.path.join(BASE, 'tools', 'build_apk26.py'), 'w', encoding='utf-8', newline='\n').write(b)
print('build_apk26 written')