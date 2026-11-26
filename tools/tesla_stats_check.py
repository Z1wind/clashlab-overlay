# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat")
from clashlab import th_data
for t in ("hidden-tesla", "air-defense", "air-sweeper", "cannon", "archer-tower", "inferno-tower", "x-bow", "scattershot", "monolith"):
    st = th_data.stats(t, 16)
    print("%-16s hp=%-8.0f dps=%-8.0f range=%s size=%s" % (t, st.get("hp"), st.get("dps"), st.get("range"), st.get("size")))
