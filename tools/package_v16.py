# -*- coding: utf-8 -*-
import hashlib, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
src = os.path.join(BASE, 'dist_exe', 'ClashLabAnnotator.exe')
dst = os.path.join(BASE, 'dist', 'ClashLabAnnotator_Desktop_v1.6.exe')
shutil.copyfile(src, dst)
data = open(dst, 'rb').read(); md5 = hashlib.md5(data).hexdigest()
print('EXE', len(data), 'md5', md5)
doc = [
'# ClashLab 桌面标注器 v1.6（Windows EXE，无需 Python）',
'',
'## v1.6：预标注三种模式',
'- 顶部「模式：标准/多标/少错」循环切换',
'  - 标准：约 72 栋（平衡）',
'  - 多标：约 87 栋（召回优先，多删误报）',
'  - 少错：约 47 栋（精度优先，自己补更多）',
'- 模型同 v1.5（混合门控+特征比对），只是阈值不同',
'- EXE ' + format(len(data), ',') + ' bytes',
'',
'## 验证（打包环境 smoke2，b03）',
'- standard n=72 / recall n=87 / precise n=47，均 ok=true',
]
open(os.path.join(BASE, 'docs', 'DESKTOP_APP.md'), 'w', encoding='utf-8', newline='\n').write('\n'.join(doc) + '\n')
print('doc updated')