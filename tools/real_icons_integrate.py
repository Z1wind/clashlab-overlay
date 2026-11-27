# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"

# 1) units 页面优先真实图标
p = os.path.join(BASE, "tools", "build_units_page.py")
t = open(p, encoding="utf-8").read()
if "units_real" not in t:
    old = '''def make_icon(item, size=96):'''
    new = '''REAL_DIR = os.path.join(BASE, "assets", "units_real")


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


def make_icon(item, size=96):'''
    t = t.replace(old, new, 1)
    # 优先真实图标
    t = t.replace('''for it in troops + spells + heroes:
    icon_path[it["id"]] = make_icon(it)''',
'''for it in troops + spells + heroes:
    rp = real_icon(it)
    icon_path[it["id"]] = rp or make_icon(it)''')
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("builder prefers real icons")

# 2) 设置页加「打开兵种/法术表」按钮
p2 = os.path.join(BASE, "clashlab", "overlay", "pages.py")
t2 = open(p2, encoding="utf-8").read()
if "open_units" not in t2:
    anchor = '''    # ---- 面板位置（外置窗口）'''
    add = '''    # ---- 兵种/法术表（内置页面，浏览器打开）----
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
    if _btn(_L(ready, "打开兵种/法术表", "Open troop/spell table"), imgui.ImVec2(160.0, 26.0), key="open_units"):
        try:
            import os as _os
            _cand = [_os.path.join(root, "dist", "units.html"), _os.path.join(root, "out", "units.html")]
            _hit = next((c for c in _cand if _os.path.exists(c)), None)
            if _hit and hasattr(_os, "startfile"):
                _os.startfile(_hit)
                ctx.log("units: opened " + _hit)
            else:
                ctx.log("units: page not found (run tools/build_units_page.py)")
        except Exception as e:
            ctx.log(f"units: open failed {e!r}")
    y += 30.0

''' + anchor
    if anchor in t2:
        t2 = t2.replace(anchor, add, 1)
        open(p2, "w", encoding="utf-8", newline="\n").write(t2)
        print("panel open_units button added")
    else:
        print("panel anchor miss")

# 3) 构建时把 units.html 放进 dist
p3 = os.path.join(BASE, "build_overlay.ps1")
t3 = open(p3, encoding="utf-8").read()
if "units.html" not in t3:
    t3 = t3.replace('$sw.Stop()',
'''if (Test-Path "$root\\out\\units.html") {
    Copy-Item "$root\\out\\units.html" "$root\\dist\\units.html" -Force
    Write-Host "[units] dist\\units.html copied"
}
$sw.Stop()''')
    open(p3, "w", encoding="utf-8", newline="\n").write(t3)
    print("build script copies units.html")

# 4) 版本 0.3.4
import re
p4 = os.path.join(BASE, "clashlab", "__init__.py")
t4 = open(p4, encoding="utf-8").read()
t4 = re.sub(r'__version__ = "[^"]+"', '__version__ = "0.3.4"', t4)
open(p4, "w", encoding="utf-8", newline="\n").write(t4)
print("version 0.3.4")
