# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "push_changes.py")
t = open(p, encoding="utf-8").read()
old = '''commit = call("POST", REPO + "/git/commits", {"message": "docs: trim comments, bilingual README/tutorial/attributions",
                                                "tree": tree["sha"], "parents": [head_sha]})'''
new = '''def _local_commit_message():
    try:
        r = subprocess.run([git, "log", "-1", "--pretty=%B"], cwd=BASE, capture_output=True, text=True)
        m = (r.stdout or "").strip()
        return m or "chore: sync workspace"
    except Exception:
        return "chore: sync workspace"


MSG = _local_commit_message()
print("commit message:", (MSG.splitlines() or [""])[0][:80], flush=True)
commit = call("POST", REPO + "/git/commits", {"message": MSG,
                                              "tree": tree["sha"], "parents": [head_sha]})'''
if old in t:
    t = t.replace(old, new)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("push_changes patched")
else:
    print("anchor miss")
