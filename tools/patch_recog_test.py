# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
p = os.path.join(BASE, 'tests', 'test_recog_model.py')
t = open(p, encoding='utf-8').read()
old = '''        if not os.path.exists(CKPT):
            raise AssertionError(
                "checkpoint 不存在：%s\\n先跑 python tools/train_save_model.py" % CKPT)
        from clashlab.recog_model import load_model
        cls.model = load_model()'''
new = '''        if not os.path.exists(CKPT):
            raise AssertionError(
                "checkpoint 不存在：%s\\n先跑 python tools/train_save_model.py" % CKPT)
        try:
            import torch  # noqa: F401
            from clashlab.recog_model import load_model
        except ImportError as exc:  # torch 是可选的推理/训练依赖，CI 不装
            raise unittest.SkipTest("推理依赖未安装（可选）：%s；跳过" % exc)
        cls.model = load_model()'''
if old in t:
    t = t.replace(old, new)
    open(p, 'w', encoding='utf-8', newline=chr(10)).write(t)
    print('patched test_recog_model.py')
else:
    print('anchor miss')
