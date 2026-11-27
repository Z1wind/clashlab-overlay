# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "build_units_page.py")
t = open(p, encoding="utf-8").read()
# 用 token 替换，避免 % 格式化与 CSS 冲突
old_start = t.index('html = """<!doctype html>')
old_end = t.index('open(out, "w", encoding="utf-8", newline="\\n").write(html)')
new_block = '''html = """<!doctype html><html><head><meta charset="utf-8"><title>ClashLab 兵种/法术数据</title>
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
'''
t = t[:old_start] + new_block + t[old_end:]
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("script patched")
