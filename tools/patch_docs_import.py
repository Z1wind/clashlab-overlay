# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"

def patch(rel, anchor, add):
    p = os.path.join(BASE, rel)
    txt = open(p, encoding="utf-8").read()
    if "import_base" in txt:
        print("skip", rel); return
    i = txt.find(anchor)
    if i < 0:
        print("ANCHOR MISS", rel); return
    txt = txt[:i] + add + "\n" + txt[i:]
    open(p, "w", encoding="utf-8", newline="\n").write(txt)
    print("patched", rel)

patch("README.md", "- **base link 调研**：",
      "- **游戏内导入**：在模拟器里点开阵型链接，运行 python tools/import_base.py --th 16 --id 07 → 自动截屏、44×44 标定，生成 base.png + layout_draft.json，再交给标注工具微调。")

patch("docs/教程.md", "## 13. 排障",
"""## 13. 从游戏导入新阵（游戏内点开链接）

    python tools/import_base.py --th 16 --id 07

在模拟器里先把分享链接点开、进到阵型预览画面，再运行上面命令（默认用 ADB 截屏；也可 --from-file 截图.png）：

- 自动检测草地边界做 44×44 标定，输出 bases/th16/07/base.png 和 layout_draft.json；
- out/import/07_grid.png 是标定可视化，先肉眼确认网格贴合；
- 标定面积只占画面很小比例时会提示 WARN（说明截的不是游戏内村庄画面）；
- 想用相近阵型预填建筑：加 --copy-from bases/th16/03/layout.json；
- 随后 python tools/annotate/start.py 微调草稿即可。

""")

patch("docs/TUTORIAL_en.md", "## 13. Troubleshooting",
"""## 13. Import a new base from the game (open the link in-game)

    python tools/import_base.py --th 16 --id 07

Open the shared layout link in the emulator, get to the base preview, then run the command above (ADB screencap by default; --from-file shot.png also works):

- Detects the grass boundary for a 44x44 calibration and writes bases/th16/07/base.png + layout_draft.json;
- out/import/07_grid.png visualises the grid for a quick check;
- A WARN is printed when the quad covers too little of the frame (the screenshot is not an in-game village);
- Seed buildings from a similar layout with --copy-from bases/th16/03/layout.json;
- Then refine the draft with python tools/annotate/start.py.

""")

p = os.path.join(BASE, "CHANGELOG.md")
t = open(p, encoding="utf-8").read()
if "import_base" not in t:
    t = t.replace("## v0.1.1 (unreleased)",
                  "## v0.1.1 (unreleased)\n\n- tools/import_base.py：游戏内点开阵型链接 → 截屏 → 自动 44x44 标定 → 生成 base.png + layout_draft.json（含标定合理性检查）。", 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("patched CHANGELOG.md")
