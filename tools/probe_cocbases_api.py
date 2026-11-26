# -*- coding: utf-8 -*-
import json, urllib.request, urllib.parse
def get(u):
    req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 clashlab"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))
for u in ("https://cocbases.com/wp-json/wp/v2/base?per_page=3",
          "https://cocbases.com/wp-json/wp/v2/base?per_page=3&_fields=id,title,link,featured_media,meta,acf"):
    try:
        d = get(u)
        print("==", u, "->", type(d).__name__, len(d) if isinstance(d, list) else d)
        if isinstance(d, list) and d:
            print(json.dumps(d[0], ensure_ascii=False)[:1200])
    except Exception as e:
        print("==", u, "ERR", str(e)[:120])
