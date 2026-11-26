# -*- coding: utf-8 -*-
import urllib.request, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
def fetch(u):
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 clashlab"})
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, r.read().decode("utf-8", "ignore")
    except Exception as e:
        return "ERR", str(e)[:70]
def text(body):
    b = re.sub(r"<script.*?</script>", " ", body, flags=re.S)
    b = re.sub(r"<style.*?</style>", " ", b, flags=re.S)
    b = re.sub(r"<[^>]+>", " ", b)
    return re.sub(r"\s+", " ", b)
for u in ("https://coc.guide/equipment/giant-arrow/",
          "https://coc.guide/defense/hidden-tesla/",
          "https://coc.guide/defenses/hidden-tesla/",
          "https://coc.guide/troop/giant-arrow/"):
    st, body = fetch(u)
    print("==", u, st)
    if st == 200:
        t = text(body)
        print("   ", t[:700].replace("\n"," "))
        for kw in ("tesla", "invisible", "Giant Arrow", "damage"):
            i = t.lower().find(kw.lower())
            if i > 0:
                print(">>", kw, ":", t[max(0,i-150):i+300])
