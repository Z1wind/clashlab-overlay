# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
p = os.path.join(BASE, 'tools', 'preannotate_core.py')
t = open(p, encoding='utf-8').read()
# 对齐训练时的裁剪约定：warp(cx,cy) 的窗口中心 = cx+0.5
t = t.replace('crops = [_crop(img, cal, cx + .5, cy + .5, self.size) for (cx, cy) in cs]',
              'crops = [_crop(img, cal, cx, cy, self.size) for (cx, cy) in cs]')
t = t.replace('crops = [_crop(img, cal, cx + .5, cy + .5, self.size) for (cx, cy) in cs]',
              'crops = [_crop(img, cal, cx, cy, self.size) for (cx, cy) in cs]')
open(p, 'w', encoding='utf-8', newline='\n').write(t)
print('crop offset patched; count remaining cx+.5:', t.count('cx + .5, cy + .5'))