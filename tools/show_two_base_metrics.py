# -*- coding: utf-8 -*-
import json, os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
m = json.load(open(os.path.join(BASE, "models", "two_bases", "metrics.json"), encoding="utf-8"))
print("within:", m.get("within_5fold"), "\nlobo:", m.get("lobo"), "\ndata n:", (m.get("data") or {}).get("n_samples"),
      "classes:", (m.get("data") or {}).get("n_classes"))
print("per_class:", json.dumps((m.get("data") or {}).get("per_class"), ensure_ascii=False)[:900])
