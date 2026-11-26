# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
p = os.path.join(BASE, "README.md")
t = open(p, encoding="utf-8").read()
add = ("- **本地网页标注器**：" + BT + "python tools/annotate_web.py --image out/live/enemy_scout_live.png" + BT +
       " → 浏览器点 4 角 + 建筑 → 导出 annotated JSON（docs/ANNOTATE_WEB.md）。\n"
       "- **敌方阵型流水线**：" + BT + "python tools/enemy_pipeline.py --layout X_annotated.json" + BT +
       " → 评分/弱点 + 穿云箭最优线 + 落点敏感性，一次输出。\n")
if "本地网页标注器" not in t:
    anchor = "## 🗺 路线图"
    t = t.replace(anchor, add + "\n" + anchor, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("README updated")

p2 = os.path.join(BASE, "CHANGELOG.md")
t2 = open(p2, encoding="utf-8").read()
if "本地网页标注器" not in t2:
    t2 = t2.replace("## v0.3.0 (unreleased)\n",
        "## v0.3.0 (unreleased)\n- 本地网页标注器 tools/annotate_web.py（4 角标定 + 建筑点选 + 导出 JSON）。\n"
        "- 敌方阵型流水线 tools/enemy_pipeline.py（评分 + 穿云箭选线 + 落点敏感性）。\n", 1)
    open(p2, "w", encoding="utf-8", newline="\n").write(t2)
    print("CHANGELOG updated")

doc = '''# 本地网页标注器（真实战图 → 可分析 JSON）

用于把「部落战侦察截图」标注成项目能读的 layout JSON。

## 用法

@@@powershell
python tools/annotate_web.py --image out/live/enemy_scout_live.png --port 8765
@@@

浏览器打开 http://127.0.0.1:8765 ：

1. 依次点**网格四个角**：左上(0,0) → 右上(44,0) → 右下(44,44) → 左下(0,44)
2. 下方选建筑类型，点该建筑**中心**（右键撤销）
3. 填名字（如 @enemy_shadow_th17@）→ 点「导出 JSON」
4. 文件写到 @@out/annotate/<名字>_annotated.json@@，直接喂给：

@@@powershell
python tools/enemy_pipeline.py --layout out\\annotate\\enemy_shadow_th17_annotated.json
@@@

## 说明

- 只用 Python 标准库，无需安装依赖；不联网、不上传图片（本机 127.0.0.1）。
- 只用点**防御/关键建筑**也能先跑评分；墙可以不用点。
- 误差要求：点击中心 ±1 格内即可（评分/选线按格中心算）。
'''.replace("@@@", BT).replace("@@", BT)
open(os.path.join(BASE, "docs", "ANNOTATE_WEB.md"), "w", encoding="utf-8", newline="\n").write(doc)
print("ANNOTATE_WEB.md written")
