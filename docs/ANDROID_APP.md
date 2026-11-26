# Android 标注 App（ClashLabAnnotator.apk）

离线标注器：内置 6 个阵图 + 已标注建筑，手机上点选/新增/改等级，导出 JSON 发回。

## 文件

- 安装包：`dist/ClashLabAnnotator.apk`（4,666,248 B，debug 签名，minSdk 24）
- 源码：`android/`（AndroidManifest.xml + java/MainActivity.java + assets/）
- 构建：`python tools/build_apk.py`（javac → d8 → aapt2 → zipalign → apksigner，不依赖 Gradle；SDK 在 `E:\tools\android-sdk`）
- 资源：`python tools/build_apk_assets.py`（从 out/annotate + bases 生成 data.js 和图片）

## 用法

1. 把 APK 传到手机安装（允许「未知来源」）
2. 打开 App → 顶部选阵 01–06
3. 点画布建筑=选中（黄圈）；点空白=按当前类型新增；拖动=移动；双指=缩放
4. 底部选类型、`Lv－/Lv＋` 改等级、删除、撤销
5. 点「导出 JSON」→ Android 10+ 会弹分享面板（可直接发微信）；文件同时写到 `下载/clash_annotate_*.json`
6. 把 JSON 发回给我 → 合并进 out/annotate 并重算 2D/推演

## 实测（LDPlayer 模拟器 Android 9）

- `adb install -r` Success；启动截图见 `android/dist/emu3.png`
- 点击选中：`#79 箭塔 (23,42)`、`Lv 21`
- 导出：`clash_annotate_2026-11-26061203.json` 13,235 B，解析后 6 阵、共 262 栋
- 未在真机实测：分享面板（Android 10+）与「下载」目录写入需要你安装后验证

## v0.2（2026-11-26 14:30 用户反馈后）

- **强制横屏**：manifest 里加 android:screenOrientation="landscape"（竖屏下画布太小、不好平移）
- **建筑圆点旁显示文字标签**：类型中文名 + 等级（如「X连弩11」「大本营16」「金矿17」），带深色底；重叠时自动避让，选中的必显示
- 修了一个缩放 bug：画布初始化时 clientWidth 可能为 0，fit 缩放被算成 0.2，标签按阈值全部隐藏；现在用窗口尺寸兜底 + 布局完成后再 fit 一次
- 打包路径统一：构建产物先出到 `android/dist/`，再同步到 `dist/ClashLabAnnotator.apk`（之前交付路径拿到的是旧 APK）

## v0.1

- 首次可安装版本：内置 6 阵、点选/新增/拖动、等级、导出 JSON、分享面板（Android 10+）
