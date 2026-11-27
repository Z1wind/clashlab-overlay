# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
wl = '\n'.join([
 '', '## 通宵轮次 3（2026-11-28 02:20-02:40）', '',
 '### CI 构建 APK —— 已接入并跑通',
 '- 新增可移植构建脚本 tools/build_apk_ci.py（读 JAVA_HOME/ANDROID_HOME，Win/Linux 通用）',
 '- 新增 .github/workflows/build-apk.yml（JDK17 + Android SDK 34，构建并上传 artifact），推送即触发',
 '- GitHub API 推送可行，run 1989763a 成功',
 '- 发现 CI artifact 仅 55KB：根因是 20 张阵图被 .gitignore 第 61 行 android/assets/img/ 忽略、仓库中不存在',
 '  -> 已 git add -f 20 张图并推送（commit 52ee008），CI 自动重跑（run 52ee008b）', '',
 '### Release v0.3.7',
 '- 已创建，资产：APK v0.2.5（8,292,385）+ units.html + 样例包 v2 + ClashOverlay.exe', '',
 '### 待办',
 '- 确认新 CI 构建 APK 尺寸恢复约 8.3MB 并校验 md5',
 '- 登记验证 + 早晨简报',
])
open(os.path.join(BASE, 'docs', 'WORKLOG.md'), 'a', encoding='utf-8', newline='\n').write(wl)
print('worklog appended')
brief = '\n'.join([
 '# 早晨简报（2026-11-28 通宵）', '',
 '## 现在的可用状态',
 '- APK v0.2.5：四角可拖、双击放大、类型收起为一行、46 类全中文、沿用上张四角、全清空、导出 v2',
 '- 桌面端：一键战报 HTML、标注器、units 页',
 '- 待你操作：装 APK 标 10 张 -> 导出 annot_all.json -> 我训练类型识别', '',
 '## 通宵完成',
 '1. copy link 解码证伪（24B 服务端引用，无坐标）',
 '2. 20 张图与来源 id 映射恢复（20/20），据此定位历史 GT 偏移 1-2 格',
 '3. 自动识别两条路线证伪（模板匹配 TP=0、格点分类器塌缩）',
 '4. APK v0.2.5 三个新功能实测 + 发布',
 '5. 可移植构建脚本 + GitHub Actions 自动构建 + Release v0.3.7', '',
 '## 已知问题',
 '- 渲染图手工标注存在系统性偏移（历史 quad 不准），暂不做自动预标注',
 '- Android 9 导出可能落 App 私有目录；Android 10+ 正常', '',
 '## 待决策',
 '- 政策风险改造是否启动：删 ADB 自动侦察/覆盖层降级/改名/去 Supercell 素材',
 '- 标注目标是否仍先 10 张冲阶段 A',
])
open(os.path.join(BASE, 'docs', 'MORNING_BRIEF.md'), 'w', encoding='utf-8', newline='\n').write(brief)
print('brief written')