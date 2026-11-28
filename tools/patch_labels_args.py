# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
# label_qa: nargs+ 支持
p = os.path.join(BASE, "tools", "label_qa.py")
t = open(p, encoding="utf-8").read()
t = t.replace('    ap.add_argument("--labels", required=True)',
              '    ap.add_argument("--labels", nargs="+", required=True)', 1)
t = t.replace('    files = [x.strip() for x in a.labels.replace("\\n", ";").split(";") if x.strip()]',
              '    files = []\n'
              '    for chunk in a.labels:\n'
              '        for x in chunk.replace("\\n", ";").split(";"):\n'
              '            if x.strip(): files.append(x.strip())', 1)
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("label_qa nargs patched")
# train_hybrid_full / train_pipeline_full: env split 支持换行
for name in ("train_hybrid_full.py", "train_pipeline_full.py"):
    q = os.path.join(BASE, "tools", name)
    s = open(q, encoding="utf-8").read()
    s = s.replace('paths = [x for x in env.split(";") if x.strip()]',
                  'import re as _re\n    paths = [x for x in _re.split(r"[;\\r\\n]+", env) if x.strip()]')
    s = s.replace('    paths = [x for x in env.split(";") if x.strip()]',
                  '    import re as _re\n    paths = [x for x in _re.split(r"[;\\r\\n]+", env) if x.strip()]')
    open(q, "w", encoding="utf-8", newline="\n").write(s)
print("env split patched")
