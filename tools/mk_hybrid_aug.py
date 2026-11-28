# -*- coding: utf-8 -*-
"""生成增强加强版混合 CV 脚本（透视 + 遮挡 + 颜色）。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
src = os.path.join(BASE, "tools", "train_hybrid_cv.py")
t = open(src, encoding="utf-8").read()
old = '''def aug(c, r):
    x = c.astype(np.float32)*r.uniform(0.85,1.15)+r.uniform(-12,12); x=np.clip(x,0,255)
    M = cv2.getRotationMatrix2D((S/2,S/2), r.uniform(-4,4), r.uniform(0.92,1.08))
    M[0,2]+=r.uniform(-3,3); M[1,2]+=r.uniform(-3,3)
    x = cv2.warpAffine(x, M, (S,S), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return x.astype(np.uint8)'''
new = '''def aug(c, r):
    x = c.astype(np.float32)*r.uniform(0.80,1.20)+r.uniform(-16,16); x=np.clip(x,0,255)
    x = x.astype(np.uint8)
    if r.random() < 0.5:
        d = int(S*0.07)
        srcp = np.float32([[0,0],[S,0],[S,S],[0,S]])
        dstp = srcp + np.float32([[r.randint(0,d),r.randint(0,d)],[r.randint(-d,0),r.randint(0,d)],
                                  [r.randint(-d,0),r.randint(-d,0)],[r.randint(0,d),r.randint(-d,0)]])
        M = cv2.getPerspectiveTransform(srcp, dstp)
        x = cv2.warpPerspective(x, M, (S,S), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    M2 = cv2.getRotationMatrix2D((S/2,S/2), r.uniform(-6,6), r.uniform(0.88,1.12))
    M2[0,2]+=r.uniform(-4,4); M2[1,2]+=r.uniform(-4,4)
    x = cv2.warpAffine(x, M2, (S,S), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    if r.random() < 0.35:
        for _ in range(r.randint(1,2)):
            w = r.randint(12,28)
            x0 = r.randint(0, S-w); y0 = r.randint(0, S-w)
            x[y0:y0+w, x0:x0+w] = r.randint(0,255)
    return x.astype(np.uint8)'''
if old in t:
    t = t.replace(old, new, 1)
    t = t.replace('out\\\\hybrid_report.json', 'out\\\\hybrid_aug_report.json')
    t = t.replace('hybrid_report.json', 'hybrid_aug_report.json')
    open(os.path.join(BASE, "tools", "train_hybrid_cv_aug.py"), "w", encoding="utf-8", newline="\n").write(t)
    print("train_hybrid_cv_aug.py written")
else:
    print("aug anchor miss")
