# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "annotator.py")
t = open(p, encoding="utf-8").read()
if "battle-report" not in t:
    anchor = '''        if path == "/candidates":'''
    add = '''        if path == "/battle-report":
            n = int(self.headers.get("Content-Length") or 0)
            try:
                doc = json.loads(self.rfile.read(n).decode("utf-8"))
            except Exception:
                return self._send(400, '{"ok":false,"error":"bad json"}', "application/json")
            try:
                from clashlab import battle_report
                name = str(doc.get("name") or "current").replace("/", "_")
                out = os.path.join(ROOT, "out", "reports", name + "_battle.html")
                r = battle_report.build(None, layout=doc.get("layout") or {}, out_path=out,
                                        th=int(doc.get("th") or 16))
                return self._send(200, json.dumps(r, ensure_ascii=False), "application/json")
            except Exception as e:
                return self._send(200, json.dumps({"ok": False, "error": str(e)[:200]}), "application/json")
''' + anchor
    if anchor in t:
        t = t.replace(anchor, add, 1)
        # 页面按钮
        t = t.replace('<button id="candbtn"', '<button id="brbtn">战报 HTML</button>\n  <button id="candbtn"')
        t = t.replace("document.getElementById('candbtn').onclick=function(){",
'''document.getElementById('brbtn').onclick=function(){
  var lay={name:(document.getElementById('name').value||'current'),grid:44,
           buildings:buildings.map(function(b){return {type:b.type,tile:b.tile};}),walls:walls};
  fetch('/battle-report',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({name:lay.name,layout:lay,th:16})})
   .then(function(r){return r.json();}).then(function(j){
     document.getElementById('report').textContent = j.ok ? ('战报已生成: '+j.path+' ('+j.bytes+' bytes)') : ('战报失败: '+j.error);
   });
};
document.getElementById('candbtn').onclick=function(){''')
        open(p, "w", encoding="utf-8", newline="\n").write(t)
        print("annotator battle-report route+button")
    else:
        print("anchor miss")
