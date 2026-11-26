# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "ocr_screen.py")
t = open(p, encoding="utf-8").read()
if "UI_LABELS" not in t:
    t = t.replace('''_LEVEL_RE = re.compile''',
'''# 游戏 UI 文案：不是对手名字/部落，解析前先剔除
UI_LABELS = {"防守", "进攻", "攻击", "部落冲突", "挂机助手", "回放", "放弃", "结束",
             "胜利", "失败", "观战", "对局", "实时", "剩余", "摧毁率", "离战斗结束还有"}
_LEVEL_RE = re.compile''')
    t = t.replace('''    texts = []
    for ln in lines:
        t = ln.get("text") if isinstance(ln, dict) else ln
        t = _clean(t)
        if t:
            texts.append(t)''',
'''    texts = []
    for ln in lines:
        t = ln.get("text") if isinstance(ln, dict) else ln
        t = _clean(t)
        if t and t not in UI_LABELS:
            texts.append(t)''')
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("ui label filter added")
else:
    print("already")

# 追加测试
pp = os.path.join(BASE, "tests", "test_ocr_screen.py")
s = open(pp, encoding="utf-8").read()
add = '''

    def test_ui_labels_dropped(self):
        from clashlab.ocr_screen import _parse_lines
        got = _parse_lines(["防守", "cHetzz", "Wrath of Kings"])
        self.assertEqual(got["name"], "cHetzz")
        self.assertEqual(got["clan"], "Wrath of Kings")
'''
if "test_ui_labels_dropped" not in s:
    s = s.replace('''if __name__ == "__main__":''', add + '''

if __name__ == "__main__":''')
    open(pp, "w", encoding="utf-8", newline="\n").write(s)
    print("test added")
