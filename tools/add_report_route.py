# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "annotate_web.py")
t = open(p, encoding="utf-8").read()
if 'path == "/report"' not in t:
    anchor = '''    def do_POST(self):
        if urllib.parse.urlparse(self.path).path != "/save":
            return self._send(404, "not found")'''
    add = '''    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/report":
            n = int(self.headers.get("Content-Length") or 0)
            try:
                doc = json.loads(self.rfile.read(n).decode("utf-8"))
            except Exception:
                return self._send(400, '{"ok":false,"error":"bad json"}', "application/json")
            name = str(doc.get("name") or "enemy").replace("/", "_").replace("\\\\", "_")
            lay = os.path.join(STATE.get("out_dir") or os.path.join(ROOT, "out", "annotate"), name + "_annotated.json")
            if not os.path.exists(lay):
                return self._send(200, json.dumps({"ok": False, "error": "layout not saved: " + lay}), "application/json")
            out_dir = os.path.join(ROOT, "out", "enemy_report", name + "_web")
            r = subprocess.run([sys.executable, "-u", os.path.join(ROOT, "tools", "report_one.py"),
                                "--layout", lay, "--out", out_dir], capture_output=True, text=True)
            summary = ""
            sp = os.path.join(out_dir, "summary.md")
            if os.path.exists(sp):
                summary = open(sp, encoding="utf-8").read()
            ok = r.returncode == 0 and bool(summary)
            return self._send(200, json.dumps({"ok": ok, "summary": summary or (r.stderr or r.stdout)[-600:],
                                               "report": out_dir}), "application/json")
        if path != "/save":
            return self._send(404, "not found")'''
    if anchor in t:
        t = t.replace(anchor, add, 1)
        print("/report route added")
    else:
        print("route anchor miss")
else:
    print("route exists")
open(p, "w", encoding="utf-8", newline="\n").write(t)
