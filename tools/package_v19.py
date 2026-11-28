# -*- coding: utf-8 -*-
import hashlib, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
src = os.path.join(BASE, 'dist_exe', 'ClashLabAnnotator.exe')
dst = os.path.join(BASE, 'dist', 'ClashLabAnnotator_Desktop_v1.9.exe')
shutil.copyfile(src, dst)
data = open(dst, 'rb').read(); md5 = hashlib.md5(data).hexdigest()
print('EXE', len(data), 'md5', md5)
doc = [
'# ClashLab 桌面标注器 v1.9（Windows EXE，无需 Python）',
'',
'## v1.9：少错模式升级（半格相位合并）',
'- 少错模式改用「整数格 + 半格」双相位扫描 + 高阈值：b03 P92.5/R81.3/type98.6（原 .92/.92 单相位 P90.3/R71.4）',
'- 代价：推理约 4.8 秒（标准 2.4 秒）',
'- 标准/多标模式不变',
'- 打包三档栋数：90 / 106 / 81',
'- EXE ' + format(len(data), ',') + ' bytes',
'',
'## 三种模式怎么选',
'- 标准：90 栋，平衡，日常用',
'- 多标：106 栋，召回最高（92%），漏得少但要多删误报',
'- 少错：81 栋，精度最高（92.5%），慢一倍但改动最少',
]
open(os.path.join(BASE, 'docs', 'DESKTOP_APP.md'), 'w', encoding='utf-8', newline='\n').write('\n'.join(doc) + '\n')
print('doc updated')