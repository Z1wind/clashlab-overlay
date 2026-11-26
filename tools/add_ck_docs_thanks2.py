# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
def c(s): return BT + s + BT

doc = '''# ClashKing 集成与致谢

## 公开端点（无需登录，已接入）

| 端点 | 用途 | 本项目位置 |
|---|---|---|
| @@@/v2/player/search?query=@@@ | 名字→tag/TH/部落 | @@clashlab/cocapi.py: search_player@@ |
| @@@/v2/clan/search?query=@@@ | 部落名→tag | @@search_clan@@ |
| @@@/v2/clan/{tag}/wars@@@ | 战争成员（含 TH/位置） | @@war_members@@ |
| @@@/v2/player/{tag}/war/attacks@@@ | 最近攻防记录（按 warEndTime 取最新 TH） | @@player_war_attacks / player_th@@ |

## 需要登录的布局库（实测）

| 端点 | 鉴权 | 结果 |
|---|---|---|
| @@@/v2/bases/personal@@@ | UserToken | 无 token → **HTTP 401** |
| @@@/v2/server/{id}/bases@@@ | UserToken/BotToken | 同上 |
| @@@/v2/bases/{id}/*@@@ | BotToken | 同上 |

网站 https://clashk.ing 的 **Bases** 是登录后的「布局库/分享」功能（前端 JS 里出现 @@bases.setAccessToken@@、@@layout library and engagement@@），公开页面拿不到布局。

**结论**：无 token 拿不到敌方/公共布局；有 UserToken 后可用 @@tools/ck_bases_cli.py@@ 直接拉。

## 怎么拿 token（不用懂英文）

1. 浏览器打开 https://clashk.ing ，点 **Login with Discord** 登录（有 Discord 号即可）；
2. F12 → **Application** → **Local Storage**（或 Cookies），找 **access token**；
3. 写到本机 @@config/cocapi_token.txt@@（一行，已 gitignore），或设置环境变量 @@CLASHKING_TOKEN@@；
4. 运行 @@python tools/ck_bases_cli.py --personal@@ / @@--server <id>@@ 验证。

## 致谢

- ClashKingInc/ClashKing —— 公开战争数据 API（本项目对手 TH/战争成员自动分析基于它）；
- ClashKingInc/ClashKingBot —— 设计思路启发：用数据代替纯图像识别，实现「无脑化」；
- ClashKingInc/ClashKingAssets —— 逐级建筑素材（合成训练用；素材版权归 Supercell，见 ATTRIBUTIONS）。

仓库地址：https://github.com/ClashKingInc
'''
doc = doc.replace("@@@", BT).replace("@@", BT)
open(os.path.join(BASE, "docs", "CLASHKING.md"), "w", encoding="utf-8", newline="\n").write(doc)
print("CLASHKING.md written")

p = os.path.join(BASE, "ATTRIBUTIONS.md")
t = open(p, encoding="utf-8").read()
add = ("\n## 特别致谢 ClashKing / Special thanks to ClashKing\n\n"
       "- ClashKingInc/ClashKing — 公开战争/玩家数据 API，本项目的对手 TH/战争成员自动分析直接使用其接口（" + c("clashlab/cocapi.py") + "）；\n"
       "- ClashKingInc/ClashKingBot — 设计思路启发：数据驱动优先于纯图像识别（OCR→API 自动化的思路来源）；\n"
       "- ClashKingInc/ClashKingAssets — 逐级建筑立绘（合成训练集；版权归 Supercell，仅本地训练使用）。\n\n"
       "感谢 ClashKing 把这些接口与素材开放给社区。\n"
       "Thanks to ClashKing for the public data API and assets that make data-driven analysis possible.\n")
if "特别致谢 ClashKing" not in t:
    open(p, "w", encoding="utf-8", newline="\n").write(t.rstrip() + "\n" + add)
    print("ATTRIBUTIONS updated")

p2 = os.path.join(BASE, "README.md")
t2 = open(p2, encoding="utf-8").read()
if "## 🙏 致谢" not in t2:
    add2 = ("\n## 🙏 致谢\n\n"
            "- 公开数据与思路：[ClashKing](https://github.com/ClashKingInc/ClashKing)（战争数据 API）、"
            "[ClashKingBot](https://github.com/ClashKingInc/ClashKingBot)（数据驱动思路）、"
            "[ClashKingAssets](https://github.com/ClashKingInc/ClashKingAssets)（逐级建筑素材）；\n"
            "- 完整名单见 [ATTRIBUTIONS.md](ATTRIBUTIONS.md)，集成说明见 [docs/CLASHKING.md](docs/CLASHKING.md)。\n")
    open(p2, "w", encoding="utf-8", newline="\n").write(t2.rstrip() + "\n" + add2)
    print("README thanks added")

gi = os.path.join(BASE, ".gitignore")
g = open(gi, encoding="utf-8").read()
if "cocapi_token.txt" not in g:
    open(gi, "a", encoding="utf-8").write("\n# ClashKing 本地 token（不提交）\nconfig/cocapi_token.txt\n")
    print("gitignore token added")
