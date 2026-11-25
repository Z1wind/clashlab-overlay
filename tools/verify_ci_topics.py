# -*- coding: utf-8 -*-
import base64, hashlib, json, os, time, urllib.error, urllib.request
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
TOKEN = os.environ["GH_TOKEN"]
REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"

def call(method, url, payload=None, retries=4):
    data = json.dumps(payload).encode() if payload is not None else None
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    if data is not None:
        h["Content-Type"] = "application/json"
    for a in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=data, method=method, headers=h), timeout=60) as r:
                b = r.read().decode("utf-8", "ignore")
                return json.loads(b) if b else {}
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "ignore")
            if e.code in (403, 429, 500, 502, 503, 504) and a < retries - 1:
                time.sleep(3 * (a + 1)); continue
            return {"_err": e.code, "_body": body[:200]}

# topics
r = call("PATCH", REPO, {"topics": ["clash-of-clans", "overlay", "imgui", "computer-vision",
                                     "layout-analysis", "llm", "research-tool", "python", "mit-license"]})
print("topics:", r.get("topics", r.get("_err")), flush=True)
# CI 文件
local = open(os.path.join(BASE, ".github", "workflows", "ci.yml"), "rb").read()
c = call("GET", REPO + "/contents/.github/workflows/ci.yml")
rb = base64.b64decode(c["content"].replace("\n", "")) if "content" in c else b""
print("ci.yml local=%d B remote=%d B md5match=%s" % (len(local), len(rb),
      hashlib.md5(local).hexdigest() == hashlib.md5(rb).hexdigest()), flush=True)
time.sleep(3)
wf = call("GET", REPO + "/actions/workflows")
print("actions workflows:", wf.get("total_count"), [w.get("name") for w in wf.get("workflows", [])], flush=True)
tree = call("GET", REPO + "/git/trees/main?recursive=1")
blobs = [t for t in tree["tree"] if t["type"] == "blob"]
print("blobs:", len(blobs), "| has ci:", ".github/workflows/ci.yml" in {b["path"] for b in blobs}, flush=True)
cs = call("GET", REPO + "/commits?per_page=10")
print("commits:", len(cs), "head:", cs[0]["sha"][:10], cs[0]["commit"]["message"][:50], flush=True)
