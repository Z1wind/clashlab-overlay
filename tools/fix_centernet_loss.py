# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "centernet_mini.py")
t = open(p, encoding="utf-8").read()
t = t.replace("        ph = torch.sigmoid(out[:, :NC]); ps = out[:, NC:]",
              "        ph = torch.sigmoid(out[:, :NC]); ps = out[:, NC:NC + 2]")
t = t.replace("        mask = hm.gt(0.9).float().unsqueeze(1)",
              "        mask = (hm.max(dim=1, keepdim=True)[0] > 0.9).float()")
t = t.replace("EPOCHS = 24", "EPOCHS = 16")
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("loss patched")
