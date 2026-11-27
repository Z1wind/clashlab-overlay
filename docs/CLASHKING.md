> ⚠️ **2026-11-27 更新：此方向已关闭。** ClashKing（Clash.Ninja）管理员明确表示：模拟器属灰色地带、覆盖层可能违反 Supercell ToS，且本项目不是「通过官方 API 使用官方数据的常规工具」，因此不授予 API 权限。本项目**不再申请 token、不再接入布局库**；仅保留公开端点作为可选能力。

# ClashKing 集成与致谢

## 公开端点（无需登录，已接入）

| 端点 | 用途 | 本项目位置 |
|---|---|---|
| `/v2/player/search?query=` | 名字→tag/TH/部落 | `clashlab/cocapi.py: search_player` |
| `/v2/clan/search?query=` | 部落名→tag | `search_clan` |
| `/v2/clan/{tag}/wars` | 战争成员（含 TH/位置） | `war_members` |
| `/v2/player/{tag}/war/attacks` | 最近攻防记录（按 warEndTime 取最新 TH） | `player_war_attacks / player_th` |

## 需要登录的布局库（实测）

| 端点 | 鉴权 | 结果 |
|---|---|---|
| `/v2/bases/personal` | UserToken | 无 token → **HTTP 401** |
| `/v2/server/{id}/bases` | UserToken/BotToken | 同上 |
| `/v2/bases/{id}/*` | BotToken | 同上 |

网站 https://clashk.ing 的 **Bases** 是登录后的「布局库/分享」功能（前端 JS 里出现 `bases.setAccessToken`、`layout library and engagement`），公开页面拿不到布局。

**结论**：无 token 拿不到敌方/公共布局；有 UserToken 后可用 `tools/ck_bases_cli.py` 直接拉。

## 怎么拿 token（不用懂英文）

1. 浏览器打开 https://clashk.ing ，点 **Login with Discord** 登录（有 Discord 号即可）；
2. F12 → **Application** → **Local Storage**（或 Cookies），找 **access token**；
3. 写到本机 `config/cocapi_token.txt`（一行，已 gitignore），或设置环境变量 `CLASHKING_TOKEN`；
4. 运行 `python tools/ck_bases_cli.py --personal` / `--server <id>` 验证。

## 致谢

- ClashKingInc/ClashKing —— 公开战争数据 API（本项目对手 TH/战争成员自动分析基于它）；
- ClashKingInc/ClashKingBot —— 设计思路启发：用数据代替纯图像识别，实现「无脑化」；
- ClashKingInc/ClashKingAssets —— 逐级建筑素材（合成训练用；素材版权归 Supercell，见 ATTRIBUTIONS）。

仓库地址：https://github.com/ClashKingInc
