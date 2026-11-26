# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "touch.py")
t = open(p, encoding="utf-8").read()
if "_best_ldplayer_main" not in t:
    anchor = '''    def _find_render_window(self) -> Optional[int]:'''
    helper = '''    @staticmethod
    def _best_ldplayer_main():
        """多开时选对实例：优先标题恰为「雷电模拟器」的那台（CoC），
        其次标题含「雷电」且不带「-1/-2」后缀；都找不到就按枚举顺序。"""
        import win32gui as _g
        cands = []
        def cb(hwnd, _):
            if _g.GetClassName(hwnd) == "LDPlayerMainFrame":
                cands.append((hwnd, _g.GetWindowText(hwnd) or ""))
            return True
        _g.EnumWindows(cb, None)
        if not cands:
            return None
        def key(item):
            hwnd, title = item
            t = title.strip()
            if t == "雷电模拟器":
                return (0, len(t), hwnd)
            if "雷电" in t and not t.endswith(("-1", "-2", "-3", "-4")):
                return (1, len(t), hwnd)
            return (2, len(t), hwnd)
        cands.sort(key=key)
        return cands[0][0]

    def _find_render_window(self) -> Optional[int]:'''
    t = t.replace(anchor, helper, 1)
    t = t.replace('''        # 先在 LDPlayerMainFrame 的子窗里找 RenderWindow/TheRender
        main = self._find_by_class(["LDPlayerMainFrame"])''',
'''        # 先在 LDPlayerMainFrame 的子窗里找 RenderWindow/TheRender（多开时优先正确的实例）
        main = self._best_ldplayer_main()''')
    t = t.replace('''    def _find_main_frame(self) -> Optional[int]:
        return self._find_by_class(["LDPlayerMainFrame"])''',
'''    def _find_main_frame(self) -> Optional[int]:
        return self._best_ldplayer_main() or self._find_by_class(["LDPlayerMainFrame"])''')
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("touch target selection patched")
else:
    print("already patched")
