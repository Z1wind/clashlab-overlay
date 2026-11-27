# -*- coding: utf-8 -*-
"""本地网页标注器：战争截图 -> 点 4 角标定 -> 点建筑选类型 -> 导出 annotated JSON。

    python tools/annotate_web.py --image out/live/enemy_scout_live.png --port 8765
然后浏览器打开 http://127.0.0.1:8765

只用标准库（http.server），不需要装新依赖。导出写到 out/annotate/<name>_annotated.json。
"""
import argparse
import json
import mimetypes
import subprocess
import os
import sys
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

STATE = {"image": None, "out_dir": None}

PAGE = r"""<!doctype html><html><head><meta charset="utf-8"><title>ClashLab annotator</title>
<style>
body{margin:0;background:#14181f;color:#dde3ea;font-family:system-ui,sans-serif}
#top{padding:6px 10px;background:#1b222c;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
#status{color:#8fa3bd;font-size:13px}
#wrap{position:relative;display:inline-block}
#cv{display:block;cursor:crosshair}
#tip{position:fixed;left:10px;bottom:8px;color:#7f93ad;font-size:12px;background:#0f131899;padding:4px 8px;border-radius:6px}
button{background:#2a3340;color:#dde3ea;border:1px solid #3a4556;border-radius:6px;padding:5px 10px;font-size:13px;cursor:pointer}
button.on{background:#2e6b3e;border-color:#49a35f}
#palette button{margin:2px;padding:4px 7px;font-size:12px}
#palette{display:inline-block;max-width:900px}
#report{white-space:pre-wrap;font-size:12px;color:#9fd0ff;padding:6px 10px;max-height:150px;overflow:auto;background:#0f1318}
</style></head><body>
<div id="top">
  <b style="color:#f0b84a">ClashLab 标注器</b>
  <span id="status"></span>
  <button id="undo">撤销 (U)</button>
  <button id="clear">清空 (C)</button>
  <button id="wallbtn">画墙模式 (W)</button>
  <button id="arrowbtn">箭线预览 (A)</button>
  <input id="name" value="enemy" style="width:110px;background:#0f1318;color:#dde3ea;border:1px solid #3a4556;border-radius:5px;padding:4px">
  <button id="save">保存 JSON (S)</button>
  <button id="report" style="background:#3d5a2e;border-color:#5b8a43">保存并出报告</button>
</div>
<div id="wrap"><canvas id="cv"></canvas></div>
<div id="palette"></div>
<div id="tip">① 依次点网格四角（左上→右上→右下→左下） ② 选类型后点建筑中心 ③ 数字键 1-9 选类型，W 画墙，U 撤销，C 清空，S 保存</div>
<div id="report"></div>
<script>
var cv=document.getElementById('cv'), ctx=cv.getContext('2d');
var IMG=new Image(); IMG.src='/image';
var corners=[], buildings=[], walls=[], wallMode=false, sel='air-defense', drawingWall=false;
var arrowMode=false, arrowPts=[], arrowHits=null;
var statusEl=document.getElementById('status');
function st(){ statusEl.textContent = corners.length<4 ? ('还需 '+(4-corners.length)+' 个角') : ('已标 '+buildings.length+' 栋 / 墙段 '+walls.length); draw(); }
IMG.onload=function(){ cv.width=IMG.width; cv.height=IMG.height; restoreDraft(); st(); };
function bil(u,v){ u=Math.max(0,Math.min(1,u)); v=Math.max(0,Math.min(1,v));
  if(corners.length<4) return [u*cv.width, v*cv.height];
  var p0=corners[0],p1=corners[1],p2=corners[2],p3=corners[3];
  return [(1-u)*(1-v)*p0[0]+u*(1-v)*p1[0]+u*v*p2[0]+(1-u)*v*p3[0],
          (1-u)*(1-v)*p0[1]+u*(1-v)*p1[1]+u*v*p2[1]+(1-u)*v*p3[1]]; }
function inv(px,py){ var u=0.5,v=0.5,i,p,e0,e1,du,dv,j00,j10,j01,j11,det,dU,dV;
  for(i=0;i<40;i++){ p=bil(u,v); e0=p[0]-px; e1=p[1]-py;
    du=bil(u+1e-4,v); dv=bil(u,v+1e-4);
    j00=(du[0]-p[0])/1e-4; j10=(dv[0]-p[0])/1e-4;
    j01=(du[1]-p[1])/1e-4; j11=(dv[1]-p[1])/1e-4;
    det=j00*j11-j10*j01; if(Math.abs(det)<1e-9) break;
    dU=(e0*j11-e1*j10)/det; dV=(-e0*j01+e1*j00)/det; u-=dU; v-=dV;
    if(Math.abs(dU)+Math.abs(dV)<1e-6) break; }
  return [u,v]; }
function snap(x,y){
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
function draw(){ if(!IMG.complete) return; ctx.drawImage(IMG,0,0);
  if(corners.length===4){ ctx.strokeStyle='rgba(80,200,255,.35)'; ctx.lineWidth=1;
    var k,a,b,c,d; for(k=0;k<=44;k+=2){ a=bil(k/44,0); b=bil(k/44,1); c=bil(0,k/44); d=bil(1,k/44);
      ctx.beginPath(); ctx.moveTo(a[0],a[1]); ctx.lineTo(b[0],b[1]); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(c[0],c[1]); ctx.lineTo(d[0],d[1]); ctx.stroke(); } }
  corners.forEach(function(p,i){ ctx.fillStyle='#ffd166'; ctx.beginPath(); ctx.arc(p[0],p[1],9,0,7); ctx.fill();
    ctx.fillStyle='#111'; ctx.font='13px sans-serif'; ctx.fillText(String(i+1), p[0]+10, p[1]-8); });
  walls.forEach(function(seg){ ctx.strokeStyle='#4a7bd8'; ctx.lineWidth=4;
    ctx.beginPath(); ctx.moveTo(seg[0][0],seg[0][1]); ctx.lineTo(seg[1][0],seg[1][1]); ctx.stroke(); });
  if(arrowPts.length===1){ var pp=bil(arrowPts[0][0]/44,arrowPts[0][1]/44);
    ctx.strokeStyle='#ffd166'; ctx.lineWidth=2; ctx.beginPath(); ctx.arc(pp[0],pp[1],7,0,7); ctx.stroke(); }
  if(arrowHits && arrowHits.ok){ var a1=bil(arrowHits.from[0]/44,arrowHits.from[1]/44), a2=bil(arrowHits.to[0]/44,arrowHits.to[1]/44);
    ctx.strokeStyle='#ffd166'; ctx.lineWidth=3; ctx.beginPath(); ctx.moveTo(a1[0],a1[1]); ctx.lineTo(a2[0],a2[1]); ctx.stroke(); }
  buildings.forEach(function(b,i){ var t=b.tile; var p=bil((t[0]+1.5)/44,(t[1]+1.5)/44);
    ctx.fillStyle = b.type.indexOf('air')>=0 ? '#e84a4a' : '#50c8b4';
    ctx.fillRect(p[0]-9,p[1]-9,18,18);
    ctx.fillStyle='#fff'; ctx.font='11px sans-serif'; ctx.fillText(String(i+1), p[0]-8, p[1]+4); });
}
cv.addEventListener('click', function(ev){
  var r=cv.getBoundingClientRect(); var sx=(ev.clientX-r.left)*cv.width/r.width, sy=(ev.clientY-r.top)*cv.height/r.height;
  if(corners.length<4){ corners.push(snap(sx,sy)); saveDraft(); st(); return; }
  if(arrowMode){
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
  if(wallMode){ if(!drawingWall){ walls.push([[sx,sy],[sx,sy]]); drawingWall=true; }
    else { walls[walls.length-1][1]=[sx,sy]; drawingWall=false; } saveDraft(); st(); return; }
  var uv=inv(sx,sy); if(uv[0]<0||uv[0]>1||uv[1]<0||uv[1]>1) return;
  buildings.push({type:sel, tile:[Math.round(uv[0]*44), Math.round(uv[1]*44)]}); saveDraft(); st();
});
document.getElementById('undo').onclick=function(){ if(walls.length){walls.pop();} else if(buildings.length){buildings.pop();} else {corners.pop();} saveDraft(); st(); };
document.getElementById('clear').onclick=function(){ corners=[]; buildings=[]; walls=[]; saveDraft(); st(); };
document.getElementById('wallbtn').onclick=function(){ wallMode=!wallMode; drawingWall=false; this.classList.toggle('on', wallMode); };
document.getElementById('arrowbtn').onclick=function(){ arrowMode=!arrowMode; arrowPts=[]; this.classList.toggle('on', arrowMode); };
function payload(){ return {name: document.getElementById('name').value||'enemy', grid:44, quad:corners, buildings:buildings, walls:walls}; }
async function save(){ var r=await fetch('/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload())}); var txt=await r.text(); statusEl.textContent=txt; return txt; }
document.getElementById('save').onclick=save;
document.getElementById('report').onclick=async function(){ var t=await save();
  var nm=document.getElementById('name').value||'enemy';
  var r=await fetch('/report',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:nm})});
  var j=await r.json(); document.getElementById('report').textContent = j.ok ? j.summary : ('报告失败: '+j.error); };
document.addEventListener('keydown', function(ev){
  var k=ev.key.toLowerCase();
  if(k==='u') document.getElementById('undo').click();
  if(k==='c') document.getElementById('clear').click();
  if(k==='w') document.getElementById('wallbtn').click();
  if(k==='a') document.getElementById('arrowbtn').click();
  if(k==='s'){ ev.preventDefault(); save(); }
  if(k==='r') document.getElementById('report').click();
});
function saveDraft(){ try{ localStorage.setItem('clashlab_draft', JSON.stringify({corners:corners,buildings:buildings,walls:walls})); }catch(e){} }
function restoreDraft(){ try{ var d=JSON.parse(localStorage.getItem('clashlab_draft')||'null'); if(d&&d.corners&&d.corners.length===4){ corners=d.corners; buildings=d.buildings||[]; walls=d.walls||[]; } }catch(e){} }
fetch('/types').then(r=>r.json()).then(types=>{
  var pal=document.getElementById('palette');
  types.forEach(function(t,i){ var b=document.createElement('button'); b.textContent=(i<9?(''+(i+1)+' '):'')+t;
    b.onclick=function(){ sel=t; [].forEach.call(pal.children,function(c){c.classList.remove('on');}); b.classList.add('on'); };
    if(t===sel) b.classList.add('on'); pal.appendChild(b); });
  document.addEventListener('keydown', function(ev){ var n=parseInt(ev.key,10); if(n>=1&&n<=9&&pal.children[n-1]) pal.children[n-1].click(); });
});
</script></body></html>"""



class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="text/plain; charset=utf-8"):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path in ("/", "/index.html"):
            return self._send(200, PAGE, "text/html; charset=utf-8")
        if u.path == "/types":
            from clashlab import assets
            names = sorted(assets.STATS.keys())
            return self._send(200, json.dumps(names), "application/json")
        if u.path == "/image":
            path = STATE.get("image")
            if not path or not os.path.exists(path):
                return self._send(404, "no image")
            with open(path, "rb") as f:
                data = f.read()
            ctype = mimetypes.guess_type(path)[0] or "image/png"
            return self._send(200, data, ctype)
        return self._send(404, "not found")

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/report":
            n = int(self.headers.get("Content-Length") or 0)
            try:
                doc = json.loads(self.rfile.read(n).decode("utf-8"))
            except Exception:
                return self._send(400, '{"ok":false,"error":"bad json"}', "application/json")
            name = str(doc.get("name") or "enemy").replace("/", "_").replace("\\", "_")
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
        if path == "/arrow":
            n = int(self.headers.get("Content-Length") or 0)
            try:
                doc = json.loads(self.rfile.read(n).decode("utf-8"))
            except Exception:
                return self._send(400, '{"ok":false,"error":"bad json"}', "application/json")
            name = str(doc.get("name") or "enemy").replace("/", "_").replace("\\", "_")
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
        if path != "/save":
            return self._send(404, "not found")
        n = int(self.headers.get("Content-Length") or 0)
        try:
            doc = json.loads(self.rfile.read(n).decode("utf-8"))
        except Exception:
            return self._send(400, "bad json")
        doc.setdefault("name", "enemy")
        doc["source_image"] = STATE.get("image")
        prev = STATE.get("prev_buildings") or []
        doc["buildings"] = prev + list(doc.get("buildings") or [])
        out_dir = STATE.get("out_dir") or os.path.join(ROOT, "out", "annotate")
        os.makedirs(out_dir, exist_ok=True)
        name = str(doc["name"]).replace("/", "_").replace("\\", "_")
        path = os.path.join(out_dir, name + "_annotated.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=1)
        try:
            shown = os.path.relpath(path, ROOT)
        except ValueError:  # 跨盘符（项目在 C: junction，数据在 E:）
            shown = os.path.abspath(path)
        return self._send(200, "saved: " + shown)


def serve(image, out_dir=None, port=8765):
    STATE["image"] = os.path.abspath(image)
    STATE["out_dir"] = os.path.abspath(out_dir) if out_dir else None
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--port", type=int, default=8765)
    a = ap.parse_args()
    httpd = serve(a.image, a.out_dir, a.port)
    print("annotator: http://127.0.0.1:%d  (image=%s)" % (a.port, os.path.relpath(STATE["image"], ROOT)))
    print("Ctrl+C 退出")
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        httpd.shutdown()


if __name__ == "__main__":
    main()
