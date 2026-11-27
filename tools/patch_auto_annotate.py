# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "auto_annotate.py")
t = open(p, encoding="utf-8").read()
t = t.replace("x = torch.from_numpy(arr[i:i + 1024][:, :, :, ::-1]).permute(0, 3, 1, 2)",
              "batch = np.ascontiguousarray(arr[i:i + 1024][:, :, :, ::-1])\n        x = torch.from_numpy(batch).permute(0, 3, 1, 2)")
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("patched contiguous")
