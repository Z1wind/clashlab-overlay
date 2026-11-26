# -*- coding: utf-8 -*-
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
