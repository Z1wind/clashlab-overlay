# -*- coding: utf-8 -*-
import json, os, sys, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
TOKEN = os.environ['GH_TOKEN']; REPO = 'Z1wind/clashlab-overlay'
API = 'https://api.github.com'; UP = 'https://uploads.github.com'
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
TAG, NAME = 'v0.3.7', 'ClashLab v0.3.7 - overnight batch: APK v0.2.5 + CI build'
BODY = '\n'.join([
  '## v0.3.7（2026-11-28 凌晨批次）', '',
  '- APK v0.2.5：沿用上张四角、双击放大、全清空；类型列表收起、四角可拖、46 类全中文、导出 v2',
  '- 可移植 APK 构建脚本 tools/build_apk_ci.py（读 JAVA_HOME / ANDROID_HOME，本地与 CI 通用）',
  '- GitHub Actions 工作流 .github/workflows/build-apk.yml：推送即构建并上传 artifact',
  '- 本轮已证伪两条自动标注路线（copy link 解码 / 渲染图模板匹配），见 docs/WORKLOG.md', '',
  '> 非官方工具；请在遵守游戏条款前提下使用。',
])
FILES = [
 ('ClashLabAnnotator_20bases_v0.2.5.apk', os.path.join(BASE, 'dist', 'ClashLabAnnotator_20bases_v0.2.5.apk')),
 ('units.html', os.path.join(BASE, 'dist', 'units.html')),
 ('clashlab_sample_reports_20261127_v2.zip', os.path.join(BASE, 'out', 'backup', 'clashlab_sample_reports_20261127_v2.zip')),
 ('ClashOverlay.exe', os.path.join(BASE, 'dist', 'ClashOverlay.exe')),
]
def req(url, method='GET', data=None, ctype='application/json'):
    h = {'Authorization': 'token ' + TOKEN, 'User-Agent': 'clashlab', 'Accept': 'application/vnd.github+json'}
    if data is not None: h['Content-Type'] = ctype
    with urllib.request.urlopen(urllib.request.Request(url, data=data, method=method, headers=h), timeout=900) as r:
        return r.status, json.loads(r.read().decode('utf-8', 'ignore'))
rel = None
_, rels = req(API + '/repos/%s/releases?per_page=60' % REPO)
for x in rels:
    if x.get('tag_name') == TAG: rel = x; break
if rel is None:
    st, rel = req(API + '/repos/%s/releases' % REPO, 'POST',
                  json.dumps({'tag_name': TAG, 'name': NAME, 'body': BODY, 'draft': False, 'prerelease': False}).encode())
    print('created', st, rel['id'], flush=True)
rid = rel['id']; have = {a['name']: a for a in rel.get('assets') or []}
for name, path in FILES:
    if name in have:
        print('skip', name, have[name]['size']); continue
    print('upload', name, os.path.getsize(path), flush=True)
    with open(path, 'rb') as f: body = f.read()
    st, art = req(UP + '/repos/%s/releases/%d/assets?name=%s' % (REPO, rid, urllib.parse.quote(name)), 'POST', body, 'application/octet-stream')
    print('  ->', st, art.get('size'), flush=True)
_, rel2 = req(API + '/repos/%s/releases/%d' % (REPO, rid))
for a in rel2.get('assets') or []:
    print('ASSET', a['name'], a['size'], a['state'])