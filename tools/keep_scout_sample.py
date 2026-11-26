# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
# 只保留一份规范样本，其余标注为重复
import glob, json, shutil
OUT = os.path.join(BASE, "out", "live", "scouts")
canon = os.path.join(OUT, "scout_01_6a402f3c30.png")
keep = os.path.join(BASE, "out", "live", "war_scout_shadow_th17.png")
if os.path.exists(canon) and not os.path.exists(keep):
    shutil.copy2(canon, keep)
print("canonical:", os.path.exists(keep))
