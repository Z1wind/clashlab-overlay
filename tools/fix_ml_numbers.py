# -*- coding: utf-8 -*-
import os, re, subprocess
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
BT = chr(96)
def fix(rel, pairs):
    p = os.path.join(BASE, rel)
    t = open(p, encoding='utf-8').read()
    n = 0
    for old, new in pairs:
        if old in t:
            t = t.replace(old, new); n += 1
    if n:
        open(p, 'w', encoding='utf-8', newline=chr(10)).write(t)
    print(rel, 'replacements:', n)

fix('README.md', [
    ('（within 0.630 / LOBO 0.477；充分训练可到 0.734 / 0.641）', '（默认 40 epoch：within 0.662 / LOBO 0.503；60 epoch 可到 0.734 / 0.641）'),
])
fix('README.en.md', [
    ('(within 0.630 / LOBO 0.477; 0.734 / 0.641 with longer training)', '(40-epoch default: within 0.662 / LOBO 0.503; 0.734 / 0.641 at 60 epochs)'),
])
fix('CHANGELOG.md', [
    ('识别模型训练/推理/可行性报告（models/recog_27px.pt、docs/ML_FEASIBILITY.md）', '识别模型训练/推理/可行性报告（默认 40 epoch：within 0.662 / LOBO 0.503；models/recog_27px.pt、docs/ML_FEASIBILITY.md）'),
])

g = os.path.join(os.environ['TEMP'], 'gitportable', 'mingit', 'cmd', 'git.exe')
subprocess.run([g, 'add', '-A'], cwd=BASE, check=True)
subprocess.run([g, 'commit', '-m', 'docs: use 40-epoch checkpoint numbers (within 0.662 / LOBO 0.503)'], cwd=BASE, check=True)
print('committed')
