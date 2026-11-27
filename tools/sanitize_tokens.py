# -*- coding: utf-8 -*-
import os, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
pat = re.compile(r'ghp_[A-Za-z0-9]{20,}')
hits = []
for dp, dn, fs in os.walk(BASE):
    dn[:] = [d for d in dn if d not in ('.git','node_modules','out','dist','build','_archive','build_v7','build_v7b','build_v7c','build_v7d','build_v8','build_v9','datasets','dataset','models')]
    for f in fs:
        if not f.endswith(('.py','.ps1','.md','.yml','.yaml','.json','.txt','.sh','.bat')): continue
        p = os.path.join(dp, f)
        try: t = open(p, encoding='utf-8', errors='ignore').read()
        except Exception: continue
        if pat.search(t):
            t2 = pat.sub('GH_TOKEN_PLACEHOLDER', t)
            open(p, 'w', encoding='utf-8', newline='\n').write(t2)
            hits.append(os.path.relpath(p, BASE))
print('sanitized files:', len(hits))
for h in hits[:20]: print(' ', h)