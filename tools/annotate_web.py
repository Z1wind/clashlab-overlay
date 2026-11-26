# -*- coding: utf-8 -*-
"""本地网页标注器：战争截图 -> 点 4 角标定 -> 点建筑选类型 -> 导出 annotated JSON。

    python tools/annotate_web.py --image out/live/enemy_scout_live.png --port 8765
然后浏览器打开 http://127.0.0.1:8765

只用标准库（http.server），不需要装新依赖。导出写到 out/annotate/<name>_annotated.json。
"""
import argparse
import json
import mimetypes
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
body{background:#14181f;color:#ddd;font-family:system-ui,Segoe UI,sans-serif;margin:0}
#bar{padding:8px 12px;background:#1d232c;position:sticky;top:0;z-index:2;display:flex;gap:8px;flex-wrap:wrap;align-items:center}
#wrap{position:relative;display:inline-block;margin:8px}
canvas{display:block;max-width:96vw;height:auto;cursor:crosshair;border:1px solid #333}
button{background:#2a3340;color:#ddd;border:1px solid #3a4556;padding:4px 8px;border-radius:4px;cursor:pointer}
button.on{background:#2e6b3e;border-color:#49a35f}
input{background:#0f1318;color:#ddd;border:1px solid #3a4556;padding:3px 6px;width:160px}
#hint{color:#8fa3bd}
</style></head><body>
<div id="bar">
  <b>ClashLab 标注器</b>
  <span id="hint">① 依次点网格四个角：左上(0,0) 右上(44,0) 右下(44,44) 左下(0,44)</span>
  <span id="status"></span>
  <input id="name" value="enemy_th??"/>
  <button id="save">导出 JSON</button>
  <button id="undo">撤销</button>
  <button id="clear">清空</button>
</div>
<div id="wrap"><canvas id="cv"></canvas></div>
<div id="bar" style="position:static;margin-top:4px"><span id="palette"></span></div>
<script>
const IMG = new Image();
let corners = [], buildings = [], walls = [], mode = 'corner', sel = 'air-defense';
const cv = document.getElementById('cv'), ctx = cv.getContext('2d');
const statusEl = document.getElementById('status');
IMG.onload = () => { cv.width = IMG.width; cv.height = IMG.height; draw(); };
IMG.src = '/image';
function draw(){
  ctx.drawImage(IMG, 0, 0);
  // 网格
  if (corners.length === 4) {
    ctx.strokeStyle = 'rgba(80,200,255,.55)'; ctx.lineWidth = 1;
    for (let i = 0; i <= 44; i += 1) {
      let a = toPx(i/44, 0), b = toPx(i/44, 1), c = toPx(0, i/44), d = toPx(1, i/44);
      ctx.beginPath(); ctx.moveTo(a[0],a[1]); ctx.lineTo(b[0],b[1]); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(c[0],c[1]); ctx.lineTo(d[0],d[1]); ctx.stroke();
    }
  }
  corners.forEach(p => { ctx.fillStyle = '#ffd166'; ctx.beginPath(); ctx.arc(p[0], p[1], 6, 0, 7); ctx.fill(); });
  buildings.forEach((b, i) => {
    const p = toPx((b.tile[0]+0.5)/44, (b.tile[1]+0.5)/44);
    ctx.fillStyle = b.type === 'air-defense' ? '#e84a4a' : (b.type === 'air-sweeper' ? '#f2a23c' : '#50c8b4');
    ctx.fillRect(p[0]-7, p[1]-7, 14, 14);
    ctx.fillStyle = '#fff'; ctx.font = '10px sans-serif'; ctx.fillText(String(i+1), p[0]-3, p[1]+4);
  });
  statusEl.textContent = corners.length < 4 ? ('还需 ' + (4-corners.length) + ' 个角') : ('已标 ' + buildings.length + ' 栋');
}
function bilinear(u, v){
  const [p0, p1, p2, p3] = corners;
  const x = (1-u)*(1-v)*p0[0] + u*(1-v)*p1[0] + u*v*p2[0] + (1-u)*v*p3[0];
  const y = (1-u)*(1-v)*p0[1] + u*(1-v)*p1[1] + u*v*p2[1] + (1-u)*v*p3[1];
  return [x, y];
}
function toPx(u, v){ return bilinear(u, v); }
function invBilinear(px, py){
  let u = 0.5, v = 0.5;
  for (let k = 0; k < 30; k += 1) {
    const p = bilinear(u, v);
    const e0 = p[0]-px, e1 = p[1]-py;
    const du = bilinear(u+1e-4, v), dv = bilinear(u, v+1e-4);
    const j00 = (du[0]-p[0])/1e-4, j10 = (dv[0]-p[0])/1e-4;
    const j01 = (du[1]-p[1])/1e-4, j11 = (dv[1]-p[1])/1e-4;
    const det = j00*j11 - j10*j01;
    if (Math.abs(det) < 1e-9) break;
    const dU = ( e0*j11 - e1*j10)/det, dV = (-e0*j01 + e1*j00)/det;
    u -= dU; v -= dV;
    if (Math.abs(dU)+Math.abs(dV) < 1e-7) break;
  }
  return [u, v];
}
cv.addEventListener('contextmenu', e => e.preventDefault());
cv.addEventListener('click', e => {
  const r = cv.getBoundingClientRect();
  const x = (e.clientX-r.left) * cv.width / r.width;
  const y = (e.clientY-r.top) * cv.height / r.height;
  if (corners.length < 4) { corners.push([x, y]); draw(); return; }
  const [u, v] = invBilinear(x, y);
  if (u < -0.05 || u > 1.05 || v < -0.05 || v > 1.05) return;
  buildings.push({ type: sel, tile: [Math.round(u*44), Math.round(v*44)] });
  draw();
});
cv.addEventListener('contextmenu', () => { buildings.pop(); draw(); });
document.getElementById('undo').onclick = () => { buildings.pop(); draw(); };
document.getElementById('clear').onclick = () => { corners = []; buildings = []; draw(); };
document.getElementById('save').onclick = async () => {
  const name = document.getElementById('name').value || 'annotated';
  const payload = { name, grid: 44, quad: corners, buildings, walls };
  const r = await fetch('/save', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
  const t = await r.text();
  alert(t);
};
fetch('/types').then(r => r.json()).then(types => {
  const pal = document.getElementById('palette');
  types.forEach(t => {
    const b = document.createElement('button');
    b.textContent = t; b.onclick = () => { sel = t; [...pal.children].forEach(c => c.classList.remove('on')); b.classList.add('on'); };
    if (t === sel) b.classList.add('on');
    pal.appendChild(b);
  });
});
IMG.onerror = () => { statusEl.textContent = '图片加载失败'; };
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
        if urllib.parse.urlparse(self.path).path != "/save":
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
