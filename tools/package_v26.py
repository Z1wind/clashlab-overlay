# -*- coding: utf-8 -*-
import hashlib, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
# 清理自测页，避免打进 APK
st = os.path.join(BASE, 'android', 'assets', 'annotate7_selftest.html')
if os.path.exists(st): os.remove(st); print('selftest removed from assets')
src = r'E:\ClashLab\android\dist\ClashLabAnnotator_v26.apk'
dst = os.path.join(BASE, 'dist', 'ClashLabAnnotator_20bases_v0.2.6.apk')
shutil.copyfile(src, dst)
data = open(dst, 'rb').read()
print('APK', len(data), 'bytes md5', hashlib.md5(data).hexdigest())
BT = chr(96)
def c(s): return BT + s + BT
doc = '\n'.join([
 '# ClashLab 标注 APK v0.2.6（20 张满防阵型 · 初学者版）',
 '',
 '## v0.2.6：四角可以拖到截图外面',
 '- 画布四周留出 18% 边距，图片居中显示',
 '- 四个角点可以拖到图片边界之外（归一化坐标允许 -0.25 ~ 1.25）',
 '- 用于截图被裁掉阵型边缘、四角不在图内的情况：网格会延伸到图外',
 '- 其余保留：四角可拖、双击放大、类型列表收起、46 类全中文、沿用上张四角、全清空、导出 v2',
 '',
 '## 验证',
 '- 无头浏览器自测：off=255,117 / 图片 906x416 / 角点 outside=[-0.2,0.5] / ok=true',
 '- 截图确认：第 1 个角点画在图片左侧黑边内，网格线延伸到图外',
 '- APK 8,300,644 bytes；页面脚本 node --check 通过',
 '',
 '## 使用',
 '1. 安装后允许文件权限',
 '2. 点四角（可拖出图片）、双击放大',
 '3. 选建筑 → 点中心 → 导出',
 '',
 '## 已知限制',
 '- 本机模拟器无法启动，v0.2.6 的触屏拖拽未在真机复测（用无头浏览器验证了几何与越界逻辑）',
 '- Android 9 导出可能落 App 私有目录；Android 10+ 正常进「下载」',
])
open(os.path.join(BASE, 'docs', 'APK_20BASES.md'), 'w', encoding='utf-8', newline='\n').write(doc + '\n')
print('doc updated')