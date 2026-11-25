# -*- coding: utf-8 -*-
# 干净诊断：当前帧 vs zoom_L0 参考 ORB 位移（pa=cur, pb=ref → shift=ref-cur）
import sys, os, cv2, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v10_lib import grab, trim, orb_shift, ROOT
ref = cv2.imdecode(np.fromfile(os.path.join(ROOT, "out", "overlay", "ladder", "zoom_L0.png"), dtype=np.uint8), cv2.IMREAD_COLOR)
cur = trim(grab())
r = trim(ref)
shift, nin, ng = orb_shift(cur, r)
print("shift(ref-cur)=", shift, "inl=", nin, "good=", ng)
