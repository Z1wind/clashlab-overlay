# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)

# ---------- cocapi: token + bases ----------
p = os.path.join(BASE, "clashlab", "cocapi.py")
t = open(p, encoding="utf-8").read()
if "def auth_headers" not in t:
    add = '''

# ---------------------------------------------------------------- 可选 token（拉布局库）
_TOKEN_FILE = os.path.join(ROOT, "config", "cocapi_token.txt")


def auth_token():
    """读 CLASHKING_TOKEN 环境变量或 config/cocapi_token.txt；都没有返回空串。"""
    tok = (os.environ.get("CLASHKING_TOKEN") or "").strip()
    if tok:
        return tok
    try:
        with open(_TOKEN_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def auth_headers():
    tok = auth_token()
    h = {"User-Agent": "clashlab", "Accept": "application/json"}
    if tok:
        h["Authorization"] = "Bearer " + tok
    return h


def _auth_get(path, timeout=25):
    """带可选 token 的 GET；401 时给出中文提示。"""
    req = urllib.request.Request(API + path, headers=auth_headers())
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "ignore"))
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise RuntimeError("ClashKing 需要登录 token：把 UserToken 写入 config/cocapi_token.txt 或设 CLASHKING_TOKEN") from None
        raise


def personal_bases():
    """/v2/bases/personal：当前账号保存的阵型（需要 UserToken）。"""
    return _auth_get("/v2/bases/personal")


def server_bases(server_id):
    """/v2/server/{id}/bases：服务器布局库（需要 UserToken/BotToken）。"""
    return _auth_get("/v2/server/%s/bases" % urllib.parse.quote(str(server_id)))
'''
    t = t.rstrip() + "\n" + add
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("cocapi bases/token added")

# ---------- CLI ----------
cli = '''# -*- coding: utf-8 -*-
"""ClashKing 布局库 CLI（需要 token）。

    python tools/ck_bases_cli.py --personal
    python tools/ck_bases_cli.py --server 12345
    python tools/ck_bases_cli.py --where-token   # 怎么拿 token
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
from clashlab import cocapi  # noqa: E402


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--personal", action="store_true")
    ap.add_argument("--server", default=None)
    ap.add_argument("--where-token", action="store_true")
    a = ap.parse_args()
    if a.where_token:
        print("1) 浏览器打开 https://clashk.ing ，用 Discord 登录")
        print("2) F12 → Application → Local Storage / Cookies，找 access token（或 /v2/auth/web/discord 的返回）")
        print("3) 写入 config/cocapi_token.txt（一行，不要提交仓库），或 set CLASHKING_TOKEN=...")
        return
    try:
        if a.personal:
            print(json.dumps(cocapi.personal_bases(), ensure_ascii=False, indent=1)[:4000])
        elif a.server:
            print(json.dumps(cocapi.server_bases(a.server), ensure_ascii=False, indent=1)[:4000])
        else:
            ap.print_help()
    except Exception as e:
        print("失败:", e)


if __name__ == "__main__":
    main()
'''
open(os.path.join(BASE, "tools", "ck_bases_cli.py"), "w", encoding="utf-8", newline="\n").write(cli)
print("cli written")

# ---------- 测试 ----------
test = '''# -*- coding: utf-8 -*-
"""ClashKing 可选 token 测试（不发网络请求）。"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


class TestCkToken(unittest.TestCase):
    def setUp(self):
        os.environ.pop("CLASHKING_TOKEN", None)
        from clashlab import cocapi
        self.ck = cocapi

    def test_no_token(self):
        self.ck._TOKEN_FILE = os.path.join(ROOT, "config", "no_such_token.txt")
        self.assertEqual(self.ck.auth_token(), "")

    def test_env_token(self):
        os.environ["CLASHKING_TOKEN"] = "abc123"
        try:
            self.assertEqual(self.ck.auth_token(), "abc123")
            self.assertEqual(self.ck.auth_headers()["Authorization"], "Bearer abc123")
        finally:
            os.environ.pop("CLASHKING_TOKEN", None)

    def test_401_hint(self):
        import urllib.error
        from unittest import mock
        err = urllib.error.HTTPError("http://x", 401, "Unauthorized", None, None)
        with mock.patch("urllib.request.urlopen", side_effect=err):
            with self.assertRaises(RuntimeError) as ctx:
                self.ck._auth_get("/v2/bases/personal")
        self.assertIn("token", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
'''
open(os.path.join(BASE, "tests", "test_ck_token.py"), "w", encoding="utf-8", newline="\n").write(test)
print("tests written")
