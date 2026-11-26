# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)

# 1) keys.py 新动作 f6
p = os.path.join(BASE, "clashlab", "overlay", "keys.py")
t = open(p, encoding="utf-8").read()
if "ocr_opponent" not in t:
    t = t.replace('    {"id": "back_hud", "zh": "回 HUD", "key": "esc",',
                  '    {"id": "ocr_opponent", "zh": "识别对手", "key": "f6",\n'
                  '     "desc": "抓帧 OCR → ClashKing API 查 TH/部落战"},\n'
                  '    {"id": "back_hud", "zh": "回 HUD", "key": "esc",')
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("keys patched")

# 2) runtime.py：动作 + 后台线程
p2 = os.path.join(BASE, "clashlab", "overlay", "runtime.py")
t2 = open(p2, encoding="utf-8").read()
if "_start_ocr_job" not in t2:
    anchor = "def _dispatch_action(rt, action: str) -> None:"
    helper = '''def _start_ocr_job(rt) -> None:
    """F6：抓当前帧 → OCR → ClashKing API → 写 out/ocr_latest.json（后台线程，不阻塞渲染）。"""
    import threading

    def worker():
        try:
            frame = rt._default_grab()
            if frame is None:
                rt.log("OCR: 抓帧失败（游戏窗口不可用）")
                return
            from clashlab import ocr_job
            payload = ocr_job.run_ocr(rt.root, frame)
            rt.ocr_line = payload.get("line") or ""
            rt.log("OCR: " + rt.ocr_line)
        except Exception as e:  # noqa: BLE001 - 热键失败只记录，不崩面板
            rt.log("OCR 失败: %r" % (e,))

    threading.Thread(target=worker, daemon=True).start()


'''
    t2 = t2.replace(anchor, helper + anchor, 1)
    old = '    if action == "toggle_mode":'
    new = ('    if action == "ocr_opponent":\n'
           '        try:\n'
           '            _start_ocr_job(rt)\n'
           '        except Exception as e:  # noqa: BLE001\n'
           '            rt.log("ocr request fail: %r" % (e,))\n'
           '    elif action == "toggle_mode":')
    t2 = t2.replace(old, new, 1)
    open(p2, "w", encoding="utf-8", newline="\n").write(t2)
    print("runtime patched")

# 3) pages.py：新增对手行
p3 = os.path.join(BASE, "clashlab", "overlay", "pages.py")
t3 = open(p3, encoding="utf-8").read()
if "_opponent_line" not in t3:
    anchor3 = "def _buildings_line(state):"
    helper3 = '''_OPP_CACHE = {"key": None, "line": ""}


def _fmt_ocr_payload(payload):
    """把 out/ocr_latest.json 压成一行（纯函数，便于测试）。"""
    if not isinstance(payload, dict):
        return "对手：未识别（F6）"
    line = payload.get("line")
    if line:
        return str(line)
    th = payload.get("th")
    ocr = payload.get("ocr") or {}
    name = ocr.get("name") or "未知"
    return "对手：%s（TH%s）· OCR" % (name, th if th else "?")


def _opponent_line(state):
    """读 out/ocr_latest.json（按 mtime 缓存）；无文件给「F6 识别」。"""
    try:
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        path = os.path.join(root, "out", "ocr_latest.json")
        try:
            mtime = os.stat(path).st_mtime
        except OSError:
            return "对手：未识别（F6）"
        key = (path, mtime)
        if _OPP_CACHE.get("key") == key:
            return _OPP_CACHE.get("line") or "对手：未识别（F6）"
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        line = _fmt_ocr_payload(payload)
        _OPP_CACHE["key"] = key
        _OPP_CACHE["line"] = line
        return line
    except Exception:
        return "对手：未识别（F6）"


'''
    t3 = t3.replace(anchor3, helper3 + anchor3, 1)
    old3 = '''    imgui.text_colored(imgui.ImVec4(*SUBTLE), _buildings_line(state))
    y += 20.0'''
    new3 = '''    imgui.text_colored(imgui.ImVec4(*SUBTLE), _buildings_line(state))
    y += 20.0
    imgui.text_colored(imgui.ImVec4(*SUBTLE), _opponent_line(state))
    y += 20.0'''
    if old3 in t3:
        t3 = t3.replace(old3, new3, 1)
        open(p3, "w", encoding="utf-8", newline="\n").write(t3)
        print("pages patched")
    else:
        print("pages draw anchor miss")
