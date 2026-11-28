# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
src = os.path.join(BASE, 'tools', 'upload_exe15.py')
dst = os.path.join(BASE, 'tools', 'upload_exe16.py')
t = open(src, encoding='utf-8').read().replace('Desktop_v1.5.exe', 'Desktop_v1.6.exe')
open(dst, 'w', encoding='utf-8', newline='\n').write(t)
print('upload_exe16 ready')