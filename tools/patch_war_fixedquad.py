# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "war_base_montage.py")
t = open(p, encoding="utf-8").read()
if "DEFAULT_QUAD" not in t:
    t = t.replace('''BASE = r"C:\\Users\\Admin（无密码）\\Doubao\\chats\\2026-11-23\\new-chat"''',
'''BASE = r"C:\\Users\\Admin（无密码）\\Doubao\\chats\\2026-11-23\\new-chat"

# 侦察界面相机固定：1280x720 手工标定，按宽度等比放大
QUAD_1280 = [[640.0, 52.0], [1120.0, 352.0], [640.0, 652.0], [178.0, 352.0]]


def default_quad(w):
    s = w / 1280.0
    return [[round(x * s, 1), round(y * s, 1)] for x, y in QUAD_1280]''')
    t = t.replace('''def wall_quad(img):''', '''def wall_quad(img):  # 备用：Hough 拟合（对真实阵可能不准，默认不用）''')
    t = t.replace('''    quad, ang = wall_quad(img)''',
'''    import argparse as _ap
    quad = None; ang = None
    if _FORCE_QUAD:
        quad = np.float32(_FORCE_QUAD); ang = 0.0
    else:
        quad = np.float32(default_quad(img.shape[1]))
        # 可选：Hough 结果作为参考输出
        try:
            _hq, _ang = wall_quad(img)
            ang = _ang
            if _hq is not None and _CHECK_HOUGH:
                quad = _hq
        except Exception:
            pass''')
    # 全局参数 + CLI --quad/--hough
    t = t.replace('''def process(img_path, thr, outdir):''',
'''_FORCE_QUAD = None
_CHECK_HOUGH = False


def process(img_path, thr, outdir):''')
    t = t.replace('''    ap.add_argument("--thr", type=float, default=0.40)''',
'''    ap.add_argument("--thr", type=float, default=0.40)
    ap.add_argument("--quad", default=None, help="四点 x,y;x,y;x,y;x,y 覆盖默认固定视角")
    ap.add_argument("--hough", action="store_true", help="改用 Hough 拟合（实验）")''')
    t = t.replace('''    a = ap.parse_args()
    imgs =''','''    a = ap.parse_args()
    global _FORCE_QUAD, _CHECK_HOUGH
    if a.quad:
        _FORCE_QUAD = [[float(v) for v in part.split(",")] for part in a.quad.split(";")]
    _CHECK_HOUGH = bool(a.hough)
    imgs =''')
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("war_base_montage fixed-quad mode")
