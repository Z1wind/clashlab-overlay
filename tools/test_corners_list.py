# -*- coding: utf-8 -*-
import json, urllib.request
items = json.load(urllib.request.urlopen("http://127.0.0.1:8781/api/list"))["items"]
print("items:", len(items))
for it in items[:3] + items[-3:]:
    print("  ", it["name"], "|", it["file"], "| done", it["done"])
