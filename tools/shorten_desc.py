# -*- coding: utf-8 -*-
import json, os, urllib.request
TOKEN = os.environ["GH_TOKEN"]; REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"
h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json", "Content-Type": "application/json"}
desc = "进程外 Clash of Clans 战术辅助覆盖层：截图 → 44×44 标定 → 评分/弱点 → 战术标注/2D + 兵棋推演；OCR+API 自动识别对手；MIT。Out-of-process CoC overlay: screenshot → calibration → scoring → tactics, wargame, OCR+API, MIT."
body = json.dumps({"description": desc}).encode()
req = urllib.request.Request(REPO, data=body, method="PATCH", headers=h)
with urllib.request.urlopen(req, timeout=30) as r:
    d = json.loads(r.read().decode())
print("desc:", d.get("description")[:120])
