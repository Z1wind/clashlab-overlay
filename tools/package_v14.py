# -*- coding: utf-8 -*-
import hashlib, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
src = os.path.join(BASE, 'dist_exe', 'ClashLabAnnotator.exe')
dst = os.path.join(BASE, 'dist', 'ClashLabAnnotator_Desktop_v1.4.exe')
shutil.copyfile(src, dst)
data = open(dst, 'rb').read(); md5 = hashlib.md5(data).hexdigest()
print('EXE', len(data), 'md5', md5)
lines = [
'# ClashLab 桌面标注器 v1.4（Windows EXE，无需 Python）',
'',
'## v1.4 更新（用重标后的 8 张数据重训）',
'- 类型分类器：8 张留一 CV top1 95.4% / top3 98.2%（v1.3 为 91.0%）',
'- 预标注检测（门控+类型）：P70.4% / R53.2% / F1 0.597 / 命中类型 83.1%（v1.3 为 P71.5/R45.6/F1 .545）',
'- 内置模型已替换为 8 张重训版本；EXE ' + format(len(data), ',') + ' bytes',
'',
'## 自动预标注',
'点四角 → 顶部「自动预标注」→ 约 4-5 秒 → 自动放 60-90 栋 → 删误报/补漏',
'',
'## 验证',
'- 打包环境 smoke2：ok=true / n=67 / ms=4992（EXE 内 ONNX 推理）',
'- 页面 smoke：20 图加载、保存 ok',
]
open(os.path.join(BASE, 'docs', 'DESKTOP_APP.md'), 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
print('doc updated')