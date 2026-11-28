# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "train_hybrid_cv.py")
t = open(p, encoding="utf-8").read()
old = "                loss = lossf(arcface(emb(x), emb.weight, y), y); opt2.zero_grad(); loss.backward(); opt2.step()"
new = "                loss = lossf_emb(arcface(emb(x), emb.weight, y), y); opt2.zero_grad(); loss.backward(); opt2.step()"
t = t.replace(old, new, 1)
t = t.replace("        emb = Emb(NCLS).to(DEV); opt2 = torch.optim.AdamW(emb.parameters(), lr=2e-3, weight_decay=2e-4)",
              "        emb = Emb(NCLS).to(DEV); opt2 = torch.optim.AdamW(emb.parameters(), lr=2e-3, weight_decay=2e-4)\n        lossf_emb = nn.CrossEntropyLoss(label_smoothing=0.05)", 1)
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("hybrid loss fixed")
