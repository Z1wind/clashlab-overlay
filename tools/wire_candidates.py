# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"

# 1) server /candidates 路由
p = os.path.join(BASE, "clashlab", "annotator.py")
t = open(p, encoding="utf-8").read()
if 'path == "/candidates"' not in t:
    anchor = '''        if path == "/arrow":'''
    add = '''        if path == "/candidates":
            n = int(self.headers.get("Content-Length") or 0)
            try:
                doc = json.loads(self.rfile.read(n).decode("utf-8"))
            except Exception:
                return self._send(400, '{"ok":false,"error":"bad json"}', "application/json")
            try:
                from cluster_fallback import nothing  # noqa: F401
            except Exception:
                pass
            try:
                from clashlab import auto_candidates as _ac
                quad = doc.get("quad") or []
                if len(quad) != 4:
                    return self._send(200, json.dumps({"ok": False, "error": "需要先点 4 个角"}), "application/json")
                res = _ac.candidates(STATE.get("image"), quad, max_n=int(doc.get("max_n") or 30))
            except Exception as e:
                res = {"ok": False, "error": str(e)[:200]}
            return self._send(200, json.dumps(res, ensure_ascii=False), "application/json")
''' + anchor
    if anchor in t:
        t = t.replace(anchor, add, 1)
        print("candidates route added")
    else:
        print("candidates anchor miss")

# 2) PAGE：按钮 + 逻辑 + 绘制
if 'id="candbtn"' not in t:
    t = t.replace('<button id="arrowbtn">箭线预览 (A)</button>', '<button id="arrowbtn">箭线预览 (A)</button>\n  <button id="candbtn" title="实验性：torch 分类器候选">自动候选</button>')
    t = t.replace("var arrowMode=false, arrowPts=[], arrowHits=null;",
                  "var arrowMode=false, arrowPts=[], arrowHits=null;\nvar cands=[], candsActive=false;")
    # 点击接受候选：在 place-building 分支之前拦截
    t = t.replace("  if(wallMode){ if(!drawingWall){",
'''  if(candsActive && cands.length){
    var cx0=0;
    for(var ci=0;ci<cands.length;ci++){ var cd=cands[ci]; var cp=bil((cd.tile[0]+cd.size/2)/44,(cd.tile[1]+cd.size/2)/44);
      if(Math.abs(cp[0]-sx)<18 && Math.abs(cp[1]-sy)<18){
        buildings.push({type:cd.type, tile:cd.tile}); cands.splice(ci,1); saveDraft(); st(); return; } }
  }
  if(wallMode){ if(!drawingWall){''')
    # 绘制候选
    t = t.replace("  buildings.forEach(function(b,i){",
'''  cands.forEach(function(cd,ci){ var cp=bil((cd.tile[0]+cd.size/2)/44,(cd.tile[1]+cd.size/2)/44);
    ctx.strokeStyle='#ffd166'; ctx.lineWidth=2; ctx.strokeRect(cp[0]-14,cp[1]-14,28,28);
    ctx.fillStyle='#ffd166'; ctx.font='10px sans-serif'; ctx.fillText(String(ci+1),cp[0]-12,cp[1]-16); });
  buildings.forEach(function(b,i){''')
    # 按钮逻辑
    t = t.replace("document.getElementById('arrowbtn').onclick=function(){ arrowMode=!arrowMode; arrowPts=[]; this.classList.toggle('on', arrowMode); };",
'''document.getElementById('arrowbtn').onclick=function(){ arrowMode=!arrowMode; arrowPts=[]; this.classList.toggle('on', arrowMode); };
document.getElementById('candbtn').onclick=function(){
  if(corners.length<4){ document.getElementById('report').textContent='先点 4 个角完成标定'; return; }
  fetch('/candidates',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({quad:corners,max_n:30})})
    .then(function(r){return r.json();}).then(function(j){
      if(!j.ok){ document.getElementById('report').textContent='自动候选不可用: '+(j.error||'未知'); return; }
      cands=j.items||[]; candsActive=true; st();
      document.getElementById('report').textContent='实验候选 '+cands.length+' 个（离开角、点选接受；点击确定后人工核对）';
    });
};''')
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("page candidates wired", len(t))
