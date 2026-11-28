# -*- coding: utf-8 -*-
import hashlib, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
src = os.path.join(BASE, 'dist_exe', 'ClashLabAnnotator.exe')
dst = os.path.join(BASE, 'dist', 'ClashLabAnnotator_Desktop_v2.1.exe')
shutil.copyfile(src, dst)
data = open(dst, 'rb').read()
print('EXE', len(data), 'md5', hashlib.md5(data).hexdigest(), 'sha256', hashlib.sha256(data).hexdigest())
doc = [
'# ClashLab 桌面标注器 v2.1（Windows EXE，无需 Python）',
'',
'## v2.1：18 张标注重训（数据翻倍）',
'- 模型改用 18 张标注（b01-b08 + b10-b12,b14-b20）重训；类型 36 类',
'- b03 实测（训练集内）：标准 P91.8/R85.7/类型98.7；多标 P84.8/R92.3；少错 P94.2/R71.4',
'- 打包三模式：标准 85 / 多标 100 / 少错 77；补充预标注（已有10栋 → 补 75）',
'- EXE ' + format(len(data), ',') + ' bytes',
'',
'## 用法',
'点四角 → 自动预标注（标准/多标/少错）→ 手动修正 → 补充预标注 → 导出',
]
open(os.path.join(BASE, 'docs', 'DESKTOP_APP.md'), 'w', encoding='utf-8', newline='\n').write('\n'.join(doc) + '\n')
print('doc updated')