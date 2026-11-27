# -*- coding: utf-8 -*-
"""下载 CI artifact（跨域重定向时去掉 Authorization）并校验 APK 内容。"""
import hashlib, io, json, os, sys, urllib.request, zipfile
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ["GH_TOKEN"]; REPO = "Z1wind/clashlab-overlay"; API = "https://api.github.com"
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
class NoAuthRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new = urllib.request.Request(newurl, headers={"User-Agent": "c"})
        return new
def gh(u, accept="application/vnd.github+json"):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": accept}
    return urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=120)
runs = json.loads(gh(API + "/repos/%s/actions/runs?per_page=8" % REPO).read().decode())["workflow_runs"]
run = next(r for r in runs if r["name"] == "build-apk" and r["status"] == "completed" and r["conclusion"] == "success")
arts = json.loads(gh(API + "/repos/%s/actions/runs/%d/artifacts" % (REPO, run["id"])).read().decode())["artifacts"]
a = arts[0]
print("artifact:", a["name"], a["size_in_bytes"], "| run", run["id"], run["head_sha"][:8])
op = urllib.request.build_opener(NoAuthRedirect)
with op.open(urllib.request.Request(a["archive_download_url"], headers={"Authorization": "token " + TOKEN,
                                                                      "Accept": "application/vnd.github+json",
                                                                      "User-Agent": "c"}), timeout=300) as r:
    print("artifact download HTTP", r.status, r.reason)
    zdata = r.read()
print("zip bytes:", len(zdata))
z = zipfile.ZipFile(io.BytesIO(zdata))
apk_bytes = z.read([n for n in z.namelist() if n.endswith(".apk")][0])
open(os.path.join(BASE, "out", "ci_apk_artifact.apk"), "wb").write(apk_bytes)
print("CI APK bytes:", len(apk_bytes), "md5:", hashlib.md5(apk_bytes).hexdigest())
loc = open(os.path.join(BASE, "dist", "ClashLabAnnotator_20bases_v0.2.5.apk"), "rb").read()
print("local bytes:", len(loc), "md5:", hashlib.md5(loc).hexdigest(), "| size_equal:", len(loc) == len(apk_bytes))
z2 = zipfile.ZipFile(io.BytesIO(apk_bytes))
names = z2.namelist()
imgs = [n for n in names if n.startswith("assets/img/")]
print("CI apk entries:", len(names), "| img:", len(imgs), "| annotate6 size:", z2.getinfo("assets/annotate6.html").file_size)
h_ci = hashlib.md5(z2.read("assets/annotate6.html")).hexdigest()
z3 = zipfile.ZipFile(os.path.join(BASE, "dist", "ClashLabAnnotator_20bases_v0.2.5.apk"))
h_loc = hashlib.md5(z3.read("assets/annotate6.html")).hexdigest()
print("annotate6 md5 CI==local:", h_ci == h_loc)
