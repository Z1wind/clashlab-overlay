# -*- coding: utf-8 -*-
import os, shutil
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
selftest = os.path.join(BASE, 'out', 'apk_qa', 'annotate7_selftest.html')
dst = os.path.join(BASE, 'android', 'assets', 'annotate7_selftest.html')
shutil.copyfile(selftest, dst)
print('copied to assets')