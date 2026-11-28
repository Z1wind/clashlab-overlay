# -*- coding: utf-8 -*-
import hashlib, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
src = os.path.join(BASE, 'dist_exe', 'ClashLabAnnotator.exe')
dst = os.path.join(BASE, 'dist', 'ClashLabAnnotator_Desktop_v2.0.exe')
shutil.copyfile(src, dst)
data = open(dst, 'rb').read(); md5 = hashlib.md5(data).hexdigest()
print('EXE', len(data), 'md5', md5)
doc = [
'# ClashLab 桌面标注器 v2.0（Windows EXE，无需 Python）',
'',
'## v2.0：补充预标注（分批标注神器）',
'- 新增「补充预标注」按钮：保留已放建筑，只追加模型认为还缺的（距离已有建筑 1.2 格内的候选自动跳过）',
'- 打包环境验证：standard base n=90；带 10 栋已有时，补充结果 n=80（已自动排除那 10 栋）',
'- 三种自动预标注模式不变：标准 90 / 多标 106 / 少错 81',
'- EXE ' + format(len(data), ',') + ' bytes',
'',
'## 用法',
'1. 点四角 →「自动预标注」（选标准/多标/少错）',
'2. 手动补几个漏的/删几个错的',
'3. 再点「补充预标注」→ 只补剩下的，不会重复放',
'4. 导出',
]
open(os.path.join(BASE, 'docs', 'DESKTOP_APP.md'), 'w', encoding='utf-8', newline='\n').write('\n'.join(doc) + '\n')
print('doc updated')