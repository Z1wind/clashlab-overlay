# -*- coding: utf-8 -*-
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import Image
for name in ("ld_main", "ld_1"):
    p = os.path.join(r"out\live", name + ".png")
    im = Image.open(p)  # SaveBitmapFile writes BMP bytes
    im = im.convert("RGB")
    out = os.path.join(r"out\live", name + ".jpg")
    im.save(out, quality=88)
    print(name, im.size, "->", out)
