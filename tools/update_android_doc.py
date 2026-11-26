# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "docs", "ANDROID_APP.md")
t = open(p, encoding="utf-8").read()
add = '''
## v0.2（2026-11-26 14:30 用户反馈后）

- **强制横屏**：manifest 里加 android:screenOrientation="landscape"（竖屏下画布太小、不好平移）
- **建筑圆点旁显示文字标签**：类型中文名 + 等级（如「X连弩11」「大本营16」「金矿17」），带深色底；重叠时自动避让，选中的必显示
- 修了一个缩放 bug：画布初始化时 clientWidth 可能为 0，fit 缩放被算成 0.2，标签按阈值全部隐藏；现在用窗口尺寸兜底 + 布局完成后再 fit 一次
- 打包路径统一：构建产物先出到 @@@android/dist/@@@，再同步到 @@@dist/ClashLabAnnotator.apk@@@（之前交付路径拿到的是旧 APK）

## v0.1

- 首次可安装版本：内置 6 阵、点选/新增/拖动、等级、导出 JSON、分享面板（Android 10+）
'''.replace("@@@", chr(96))
if "v0.2（2026-11-26" not in t:
    t = t.rstrip() + "\n" + add
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("docs updated")
