# -*- coding: utf-8 -*-
import hashlib, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
src = os.path.join(BASE, 'dist_exe', 'ClashLabAnnotator.exe')
dst = os.path.join(BASE, 'dist', 'ClashLabAnnotator_Desktop_v1.7.exe')
shutil.copyfile(src, dst)
data = open(dst, 'rb').read(); md5 = hashlib.md5(data).hexdigest()
print('EXE', len(data), 'md5', md5)
doc = [
'# ClashLab 桌面标注器 v1.7（Windows EXE，无需 Python）',
'',
'## v1.7 修复：预标注裁剪中心偏移 0.5 格',
'- 训练时窗口中心 = 格子+0.5；旧版推理传了 格子+0.5，实际中心多偏 0.5 格 → 精度受损',
'- 修复后同一张图（b03，训练集内）：标准 P90.3/R71.4/类型100%；多标 P85.2/R82.4/类型96%；少错 P93.2/R60.4/类型100%',
'- 打包环境三档栋数：66 / 84 / 46，均 ok=true',
'- EXE ' + format(len(data), ',') + ' bytes',
'',
'## 用法',
'点四角 → 选模式（标准/多标/少错）→「自动预标注」→ 删误报/补漏 → 导出',
]
open(os.path.join(BASE, 'docs', 'DESKTOP_APP.md'), 'w', encoding='utf-8', newline='\n').write('\n'.join(doc) + '\n')
print('doc updated')