# -*- coding: utf-8 -*-
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
