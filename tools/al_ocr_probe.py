# -*- coding: utf-8 -*-
"""OCR 预处理试验：弹窗名称区域裁剪 + 放大，比较识别率。"""
import json, sys, time
from PIL import Image, ImageOps
import winocr

src = sys.argv[1]
out = sys.argv[2]
img = Image.open(src).convert("RGB")
crops = {
    "full": img,
    "popup": img.crop((430, 450, 860, 530)),
    "popup_x2": img.crop((430, 450, 860, 530)).resize((860, 160), Image.LANCZOS),
    "popup_x3": img.crop((430, 450, 860, 530)).resize((1290, 240), Image.LANCZOS),
    "name_line": img.crop((470, 460, 820, 500)),
    "name_line_x3": img.crop((470, 460, 820, 500)).resize((1050, 120), Image.LANCZOS),
    "name_line_x4_gray": ImageOps.autocontrast(img.crop((470, 460, 820, 500)).convert("L")).convert("RGB").resize((1400, 160), Image.LANCZOS),
}
res = {}
for k, im in crops.items():
    t0 = time.time()
    r = winocr.recognize_pil_sync(im, "zh-Hans")
    res[k] = {"sec": round(time.time() - t0, 3), "text": r.get("text", ""),
              "lines": [l.get("text", "") for l in r.get("lines", [])]}
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("done", len(res))
