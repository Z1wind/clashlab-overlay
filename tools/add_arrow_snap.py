# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "annotate_web.py")
t = open(p, encoding="utf-8").read()
orig = t

# --- A. 吸附 ---
t = t.replace("if(corners.length<4){ corners.push([sx,sy]); saveDraft(); st(); return; }",
              "if(corners.length<4){ corners.push(snap(sx,sy)); saveDraft(); st(); return; }")
# --- B. snap 函数 ---
t = t.replace("function draw(){ if(!IMG.complete) return;",
'''function snap(x,y){
  try{
    var R=18, best=null, bd=1e9;
    var data=ctx.getImageData(Math.max(0,Math.round(x-R)),Math.max(0,Math.round(y-R)),
      Math.min(2*R, cv.width-Math.max(0,Math.round(x-R))), Math.min(2*R, cv.height-Math.max(0,Math.round(y-R))));
    for(var j=0;j<data.height;j++){ for(var i=0;i<data.width;i++){
      var k=(j*data.width+i)*4, r=data.data[k], g=data.data[k+1], b=data.data[k+2];
      if(b>140 && g>105 && b>r+25){ var dx=i-R, dy=j-R, d=dx*dx+dy*dy;
        if(d<bd){ bd=d; best=[Math.max(0,Math.round(x-R))+i, Math.max(0,Math.round(y-R))+j]; } } } }
    if(best && bd<=361) return best;
  }catch(e){}
  return [x,y];
}
function draw(){ if(!IMG.complete) return;''')
# --- C. 状态变量 ---
t = t.replace("var corners=[], buildings=[], walls=[], wallMode=false, sel='air-defense', drawingWall=false;",
              "var corners=[], buildings=[], walls=[], wallMode=false, sel='air-defense', drawingWall=false;\nvar arrowMode=false, arrowPts=[], arrowHits=null;")
# --- D. 按钮 ---
t = t.replace('<button id="wallbtn">画墙模式 (W)</button>',
              '<button id="wallbtn">画墙模式 (W)</button>\n  <button id="arrowbtn">箭线预览 (A)</button>')
# --- E. 点击分支：箭线 ---
t = t.replace("  if(wallMode){ if(!drawingWall){",
'''  if(arrowMode){
    var uv2=inv(sx,sy); if(uv2[0]<0||uv2[0]>1||uv2[1]<0||uv2[1]>1) return;
    arrowPts.push([Math.round(uv2[0]*44*10)/10, Math.round(uv2[1]*44*10)/10]);
    if(arrowPts.length>2) arrowPts=[arrowPts[1],arrowPts[2]];
    if(arrowPts.length===2){
      var nm=document.getElementById('name').value||'enemy';
      fetch('/arrow',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({name:nm, from:arrowPts[0], to:arrowPts[1]})})
        .then(function(r){return r.json();}).then(function(j){
          arrowHits=j; document.getElementById('report').textContent =
            j.ok ? ('箭线 '+JSON.stringify(j.from)+'→'+JSON.stringify(j.to)+' 命中 '+j.hits+'：'+JSON.stringify(j.summary)+' 评分 '+j.score)
                 : ('箭线失败: '+j.error);
          draw();
        });
    }
    saveDraft(); st(); return;
  }
  if(wallMode){ if(!drawingWall){''')
# --- F. 绘制箭线 ---
t = t.replace("  buildings.forEach(function(b,i){",
'''  if(arrowPts.length===1){ var pp=bil(arrowPts[0][0]/44,arrowPts[0][1]/44);
    ctx.strokeStyle='#ffd166'; ctx.lineWidth=2; ctx.beginPath(); ctx.arc(pp[0],pp[1],7,0,7); ctx.stroke(); }
  if(arrowHits && arrowHits.ok){ var a1=bil(arrowHits.from[0]/44,arrowHits.from[1]/44), a2=bil(arrowHits.to[0]/44,arrowHits.to[1]/44);
    ctx.strokeStyle='#ffd166'; ctx.lineWidth=3; ctx.beginPath(); ctx.moveTo(a1[0],a1[1]); ctx.lineTo(a2[0],a2[1]); ctx.stroke(); }
  buildings.forEach(function(b,i){''')
# --- G. arrow 按钮 + 快捷键 ---
t = t.replace("document.getElementById('wallbtn').onclick=function(){ wallMode=!wallMode; drawingWall=false; this.classList.toggle('on', wallMode); };",
'''document.getElementById('wallbtn').onclick=function(){ wallMode=!wallMode; drawingWall=false; this.classList.toggle('on', wallMode); };
document.getElementById('arrowbtn').onclick=function(){ arrowMode=!arrowMode; arrowPts=[]; this.classList.toggle('on', arrowMode); };''')
t = t.replace("  if(k==='w') document.getElementById('wallbtn').click();",
              "  if(k==='w') document.getElementById('wallbtn').click();\n  if(k==='a') document.getElementById('arrowbtn').click();")
# --- H. 服务端 /arrow 路由 ---
if 'path == "/arrow"' not in t:
    anchor = '''        if path != "/save":
            return self._send(404, "not found")'''
    add = '''        if path == "/arrow":
            n = int(self.headers.get("Content-Length") or 0)
            try:
                doc = json.loads(self.rfile.read(n).decode("utf-8"))
            except Exception:
                return self._send(400, '{"ok":false,"error":"bad json"}', "application/json")
            name = str(doc.get("name") or "enemy").replace("/", "_").replace("\\\\", "_")
            lay_path = os.path.join(STATE.get("out_dir") or os.path.join(ROOT, "out", "annotate"), name + "_annotated.json")
            if not os.path.exists(lay_path):
                return self._send(200, json.dumps({"ok": False, "error": "先保存标注再预览"}), "application/json")
            try:
                lay = json.load(open(lay_path, encoding="utf-8"))
                from clashlab.overlay import giant_arrow_diagram as ga
                hits = ga.match_skewered(lay, doc.get("from"), doc.get("to"))
                out = {"ok": True, "from": doc.get("from"), "to": doc.get("to"),
                       "hits": len(hits), "summary": ga.summarize_hits(hits), "score": ga.score_hits(hits)}
            except Exception as e:
                out = {"ok": False, "error": str(e)[:200]}
            return self._send(200, json.dumps(out), "application/json")
''' + anchor
    if anchor in t:
        t = t.replace(anchor, add, 1)
        print("arrow route added")
    else:
        print("arrow route anchor miss")
if t != orig:
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("PAGE patched, len", len(t))
else:
    print("no changes!")
