# -*- coding: utf-8 -*-
"""创建 GitHub Release 并上传发布资产（exe / 源码包 / SHA256SUMS）。"""
import argparse, json, os, sys, time, urllib.error, urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.github.com"


def call(method, url, token, payload=None, raw=None, timeout=600, retries=3):
    headers = {"Authorization": "token " + token, "User-Agent": "clashlab-release",
               "Accept": "application/vnd.github+json"}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    elif raw is not None:
        data = raw
        headers["Content-Type"] = "application/octet-stream"
    last = None
    for attempt in range(retries):
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8", "ignore")
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "ignore")
            last = "HTTP %s %s" % (e.code, body[:200])
            if e.code in (403, 429, 500, 502, 503, 504):
                time.sleep(3 * (attempt + 1))
                continue
            raise RuntimeError(last)
        except Exception as e:
            last = repr(e)[:200]
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(last)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", required=True)
    ap.add_argument("--owner", default="Z1wind")
    ap.add_argument("--repo", default="clashlab-overlay")
    ap.add_argument("--tag", default="v0.1.0")
    a = ap.parse_args()
    repo_api = "%s/repos/%s/%s" % (API, a.owner, a.repo)

    meta = {"description": "An LLM-assisted Clash of Clans base-layout research tool: scout -> 44x44 calibration -> defense score -> weak points -> tactical diagram. Open source (MIT), out-of-process overlay over LDPlayer.",
            "homepage": "https://github.com/%s/%s" % (a.owner, a.repo),
            "topics": ["clash-of-clans", "overlay", "imgui", "computer-vision", "layout-analysis",
                       "llm", "research-tool", "python", "mit-license"]}
    try:
        r = call("PATCH", repo_api, a.token, meta)
        print("meta:", r.get("full_name"), "topics:", r.get("topics"), flush=True)
    except Exception as e:
        print("meta failed:", str(e)[:200], flush=True)

    body = ("First open-source release.\n\n"
            "- Out-of-process ImGui overlay (HUD/PANEL), zero injection\n"
            "- Defense score 0-100 with S-F grade and located weak points\n"
            "- Giant-arrow tactical diagram and 2D simulation in panel\n"
            "- 86 unit tests, MIT license\n\n"
            "Assets: ClashOverlay.exe (Windows x64) and source zip; verify with SHA256SUMS.txt.")
    try:
        rel = call("POST", repo_api + "/releases", a.token,
                   {"tag_name": a.tag, "name": "ClashLab v0.1.0 - LLM-assisted layout research tool",
                    "draft": False, "prerelease": False, "body": body})
        print("release:", rel["tag_name"], "id:", rel["id"], flush=True)
    except Exception as e:
        print("release failed:", str(e)[:300], flush=True)
        sys.exit(1)

    upload_base = rel["upload_url"].split("{")[0]
    for fn in ("ClashOverlay.exe", "ClashLab_open_source_v0.1.0.zip", "SHA256SUMS.txt"):
        p = os.path.join(BASE, "out", "release", fn)
        if not os.path.exists(p):
            print("SKIP", fn, flush=True)
            continue
        size = os.path.getsize(p)
        print("uploading", fn, size, "B ...", flush=True)
        try:
            with open(p, "rb") as f:
                raw = f.read()
            url = upload_base + "?name=" + urllib.parse.quote(fn)
            j = call("POST", url, a.token, raw=raw)
            print("  asset OK:", j.get("name"), j.get("size"), "B state=", j.get("state"), flush=True)
        except Exception as e:
            print("  asset FAILED:", fn, str(e)[:250], flush=True)
    print("RELEASE DONE", flush=True)


main()
