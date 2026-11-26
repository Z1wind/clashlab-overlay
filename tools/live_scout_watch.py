# -*- coding: utf-8 -*-
"""实机观察 v2：ADB screencap（只读）→ OCR 左上角；排除自己/UI 文案后当敌人解析。
等侦察界面（顶部对手名字/部落）出现，命中即调 API 落盘。"""
import json, os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat")
import numpy as np, cv2
from clashlab import ocr_screen, cocapi

ADB = r"E:\leidian\LDPlayer9\adb.exe"
DEV = "emulator-5554"
OUT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\live"
os.makedirs(OUT, exist_ok=True)
SELF_NAMES = {"z1wind", "zlwind", "小砸锤"}
BAD = ("防守", "进攻", "部落冲突", "挂机助手", "回放", "放弃", "结束", "胜利", "失败",
       "观战", "对局", "实时", "剩余", "摧毁率", "离战斗结束还有", "战斗", "建造", "商店")

def grab():
    p = os.path.join(OUT, "_adb.png")
    subprocess.run([ADB, "-s", DEV, "shell", "screencap", "-p", "/sdcard/_s.png"],
                   capture_output=True, timeout=20)
    subprocess.run([ADB, "-s", DEV, "pull", "/sdcard/_s.png", p], capture_output=True, timeout=20)
    img = cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)
    return img

start = time.time()
last = ""
while time.time() - start < 420:
    img = grab()
    if img is None or img.shape[0] < 100:
        time.sleep(3); continue
    got = ocr_screen.read_opponent(img)
    lines = [l["text"] for l in got.get("lines") or []]
    if lines != last:
        print("[ocr]", lines, flush=True); last = lines
    name = got.get("name") or ""
    clan = got.get("clan") or ""
    if name and name not in SELF_NAMES and not any(b in name for b in BAD) and len(name) >= 3 and clan:
        try:
            res = cocapi.resolve_opponent(name, clan, fresh=True, ocr_level=got.get("level"))
        except Exception as e:
            print("api fail", str(e)[:90], flush=True); time.sleep(3); continue
        # 排除自己（API 也再确认一次）
        p = res.get("player") or {}
        if p.get("name") and str(p["name"]).lower() in {n.lower() for n in SELF_NAMES}:
            print("[self]", p.get("name"), flush=True); time.sleep(3); continue
        if p.get("tag"):
            payload = {"ocr": got, "api": res, "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
            json.dump(payload, open(os.path.join(OUT, "enemy_scout.json"), "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)
            cv2.imencode(".png", img)[1].tofile(os.path.join(OUT, "enemy_scout_frame.png"))
            print("[HIT]", p.get("name"), p.get("tag"), "TH", p.get("th"), flush=True)
            break
    time.sleep(3)
print("scout watcher done", flush=True)
