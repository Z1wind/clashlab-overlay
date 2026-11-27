# -*- coding: utf-8 -*-
import hashlib, json, os, sys, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
TOKEN = os.environ['GH_TOKEN']; REPO = 'Z1wind/clashlab-overlay'; API = 'https://api.github.com'
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
NAME = 'ClashLabAnnotator_20bases_v0.2.6.apk'; PATH = os.path.join(BASE, 'dist', NAME)
def gh(u, accept='application/vnd.github+json'):
    h = {'Authorization': 'token ' + TOKEN, 'User-Agent': 'c', 'Accept': accept}
    return urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=600)
rels = json.loads(gh(API + '/repos/%s/releases?per_page=20' % REPO).read().decode())
rel = next(x for x in rels if x['tag_name'] == 'v0.3.7')
a = next(x for x in rel['assets'] if x['name'] == NAME)
print('asset', a['name'], a['size'], a['state'])
with gh(a['url'], accept='application/octet-stream') as r:
    print('download HTTP', r.status, r.reason, '| CL:', r.headers.get('Content-Length'), '| ETag:', r.headers.get('ETag'))
    data = r.read()
loc = open(PATH, 'rb').read()
print('downloaded', len(data), '| md5 match:', hashlib.md5(data).hexdigest() == hashlib.md5(loc).hexdigest(), '| md5', hashlib.md5(data).hexdigest())
for x in rel['assets']: print('LIST', x['name'], x['size'])