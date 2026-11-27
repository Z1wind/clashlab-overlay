# -*- coding: utf-8 -*-
"""生成兵种/法术/英雄图标（PNG）与可视化页面 out/units.html。"""
import base64, json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import Image, ImageDraw, ImageFont
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab import units
ICON_DIR = os.path.join(BASE, "assets", "units")
os.makedirs(ICON_DIR, exist_ok=True)
FONT_PATHS = [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\simhei.ttf"]
def font(size):
    for p in FONT_PATHS:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

REAL_DIR = os.path.join(BASE, "assets", "units_real")


def real_icon(item, size=96):
    uid = item["id"]
    for ext in (".png", ".webp", ".jpg"):
        p = os.path.join(REAL_DIR, uid + ext)
        if os.path.exists(p):
            try:
                im = Image.open(p).convert("RGBA")
                im.thumbnail((size, size), Image.LANCZOS)
                canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
                canvas.paste(im, ((size - im.width) // 2, (size - im.height) // 2), im)
                out = os.path.join(ICON_DIR, uid + "_real.png")
                canvas.save(out)
                return out
            except Exception:
                pass
    return None


def make_icon(item, size=96):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r, g, b = hex_rgb(item["color"])
    d.rounded_rectangle([2, 2, size-2, size-2], radius=18, fill=(r, g, b, 255), outline=(255, 255, 255, 70), width=2)
    # 上半高光
    d.rounded_rectangle([6, 4, size-6, size//2], radius=14, fill=(255, 255, 255, 28))
    f = font(40)
    txt = item["glyph"]
    bb = d.textbbox((0, 0), txt, font=f)
    d.text(((size - (bb[2]-bb[0]))/2 - bb[0], (size - (bb[3]-bb[1]))/2 - bb[1]), txt, font=f, fill=(255, 255, 255, 255))
    path = os.path.join(ICON_DIR, item["id"] + ".png")
    img.save(path)
    return path

def b64(p):
    return "data:image/png;base64," + base64.b64encode(open(p, "rb").read()).decode("ascii")

def card(item, extra):
    return ('<div class="card"><img src="%s"><div class="nm">%s<br><span class="en">%s</span></div>'
            '<div class="st">%s</div></div>') % (b64(icon_path[item["id"]]), item["zh"], item["en"], extra)

icon_path = {}
troops = units.troop_list(); spells = units.spell_list(); heroes = units.hero_list()
for it in troops + spells + heroes:
    rp = real_icon(it)
    icon_path[it["id"]] = rp or make_icon(it)

ROLE_ZH = {"ground": "地面", "air": "空中", "support": "辅助", "tank": "坦克", "ranged": "远程", "utility": "功能"}
troop_html = "".join(card(t, "DPS %s · HP %s · %s格 · %s" % (t["dps"], t["hp"], t["house"], ROLE_ZH.get(t["role"], t["role"]))) for t in troops)
spell_html = "".join(card(s, "半径 %s 格 · %ss · %s" % (s["radius"], s["duration"], s["use"])) for s in spells)
hero_html = "".join(card(h, "英雄") for h in heroes)

# 推荐配比（knowledge/strategies.json）
recs_html = ""
try:
    kn = json.load(open(os.path.join(BASE, "knowledge", "strategies.json"), encoding="utf-8"))
    st = kn.get("strategies") or kn
    rows = []
    if isinstance(st, dict):
        for k, v in list(st.items())[:6]:
            rows.append((k, v))
    elif isinstance(st, list):
        for v in st[:6]:
            rows.append((v.get("id") or v.get("name"), v))
    for name, v in rows:
        troops_d = (v or {}).get("troops") or {}
        spells_d = (v or {}).get("spells") or {}
        if not isinstance(troops_d, dict):
            continue
        chips = []
        for tid, c in list(troops_d.items())[:8]:
            if tid in icon_path:
                chips.append('<span class="chip"><img src="%s">%s×%s</span>' % (b64(icon_path[tid]), units.TROOPS[tid]["zh"], c))
        for sid, c in list(spells_d.items())[:6]:
            if sid in icon_path:
                chips.append('<span class="chip sp"><img src="%s">%s×%s</span>' % (b64(icon_path[sid]), units.SPELLS[sid]["zh"], c))
        recs_html += '<div class="rec"><b>%s</b> %s</div>' % (v.get("name") or name, "".join(chips))
except Exception as e:
    recs_html = "<div class='rec'>推荐配比加载失败: %s</div>" % str(e)[:120]

html = """<!doctype html><html><head><meta charset="utf-8"><title>ClashLab 兵种/法术数据</title>
<style>
body{margin:0;background:#0f1318;color:#dde3ea;font-family:system-ui,'Microsoft YaHei',sans-serif;padding:18px}
h1{color:#f0b84a;font-size:22px;margin:0 0 4px}
h2{font-size:16px;margin:22px 0 10px;color:#9fd0ff;border-left:4px solid #4a8bd6;padding-left:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px}
.card{background:#1b222c;border:1px solid #2a3340;border-radius:10px;padding:10px;display:flex;gap:10px;align-items:center}
.card img{width:54px;height:54px;border-radius:10px}
.nm{font-size:14px;font-weight:600}
.en{color:#8fa3bd;font-size:11px;font-weight:400}
.st{color:#9fb3c8;font-size:11px;margin-left:auto;text-align:right;max-width:110px}
.rec{background:#151c24;border-radius:8px;padding:8px;margin:6px 0;font-size:12px;line-height:2}
.chip{display:inline-flex;align-items:center;gap:4px;background:#222b36;border-radius:14px;padding:2px 9px 2px 3px;margin:2px 4px}
.chip img{width:22px;height:22px;border-radius:50%}
.chip.sp{background:#2a2336}
.note{color:#7f93ad;font-size:11px;margin-top:16px}
</style></head><body>
<h1>ClashLab 兵种 / 法术 / 英雄数据</h1>
<div class="note">粗粒度参考值，用于相对比较与战斗模拟；不是游戏内精确数值。</div>
<h2>兵种（__TROOPS_N__）</h2><div class="grid">__TROOPS__</div>
<h2>法术（__SPELLS_N__）</h2><div class="grid">__SPELLS__</div>
<h2>英雄（__HEROES_N__）</h2><div class="grid">__HEROES__</div>
<h2>推荐配比（知识库）</h2>__RECS__
</body></html>"""
for k, v in (("__TROOPS_N__", str(len(troops))), ("__TROOPS__", troop_html),
             ("__SPELLS_N__", str(len(spells))), ("__SPELLS__", spell_html),
             ("__HEROES_N__", str(len(heroes))), ("__HEROES__", hero_html),
             ("__RECS__", recs_html)):
    html = html.replace(k, v)
out = os.path.join(BASE, "out", "units.html")
open(out, "w", encoding="utf-8", newline="\n").write(html)
print("html", out, os.path.getsize(out), "bytes | icons:", len(icon_path))
