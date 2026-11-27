# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
src = os.path.join(BASE, 'tools', 'build_apk24.py')
t = open(src, encoding='utf-8').read()
t = t.replace('classes24','classes25').replace('dex24','dex25').replace('base24','base25').replace('aligned24','aligned25')
t = t.replace('"--version-code", "6"', '"--version-code", "7"').replace('"--version-name", "0.2.4"', '"--version-name", "0.2.5"')
t = t.replace('ClashLabAnnotator_v24.apk', 'ClashLabAnnotator_v25.apk').replace('构建 APK v0.2.4', '构建 APK v0.2.5')
open(os.path.join(BASE, 'tools', 'build_apk25.py'), 'w', encoding='utf-8', newline='\n').write(t)
print('build_apk25 written')