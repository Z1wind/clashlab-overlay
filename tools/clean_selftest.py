# -*- coding: utf-8 -*-
import hashlib, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
st = os.path.join(BASE, 'android', 'assets', 'annotate7_selftest.html')
if os.path.exists(st): os.remove(st); print('selftest removed')