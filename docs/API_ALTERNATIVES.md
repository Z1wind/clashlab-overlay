# API 可用性实测：ClashKing 免费端点 + 替代方案（2026-11-27）

> 全部结论来自本机真实请求（api.clashk.ing，无需 token / 不带 Authorization）。

## 一、ClashKing 免费（无 token）可用清单

| 端点 | 实测状态 | 返回内容 | 用途 |
|---|---|---|---|
| `/v2/player/search?query=` | 200 | name/tag/**townHallLevel**/clan | 名字→TH/clan（替代 OCR→TH 查询）|
| `/v2/clan/search?query=` | 200 | 部落列表（name/tag/members/…）| 找部落 |
| `/v2/clan/{tag}/cached` | 200 | name/level/members[{tag,name,**townHallLevel**}]/warLeague | **部落成员+TH（无需 token）** |
| `/v2/clan/{tag}/wars?limit=&type=cwl` | 200 | 已存储战争（state/startTime/teamSize/attacks）| 战争历史/对手阵容 |
| `/v2/clan/{tag}/rankings` | 200 | name/tag/homeVillage/builderBase/clanCapital | 部落排名数据 |
| `/v2/clan/{tag}/donations/summary` | 200 | from/asOf/donated/received | 捐兵统计 |
| `/v2/player/{tag}/join-leave` | 200 | 加入/离开历史 | 玩家履历 |
| `/v2/player/{tag}/activity-summary` | 200 | gold/elixir/darkElixir/donated/farmingAttacks | 活跃度（需被收录）|
| `/v2/static/{category}/names` | 200 | troops/buildings/spells/heroes/pets/equipment 名称表 | **静态数据** |
| `/v2/static/buildings/Town%20Hall/max-level` | 200 | max_level=19 | **TH19 上限**（比本地静态表新）|
| `/v2/dates/seasons` / `/v2/dates/raid-weekends` | 200 | 赛季/突袭周末日期 | 时间轴 |
| `/v2/counts/players/town-halls` | 200 | townhall_level/count | 分布统计 |
| `/v2/leaderboard/clan/win-streak` | 200 | 连胜榜 | 排行榜 |

实测样本：
- `ck_lookup.py --clan '#PUP9P88R' --wars cwl` → clan Shadow N Shadow level9 members15 warLeague Gold II；TH 分布 {13:2,12:2,11:5,...}；CWL 5 条 warEnded
- `ck_lookup.py --static 'Town Hall'` → Town Hall max_level = 19
- `ck_lookup.py --player 'z1wind'` → tag #QCRJPL2RJ th=16 clan 小砸锤

### 覆盖率注意
- `cached` 与 `wars` 只对 **ClashKing 已收录** 的部落/玩家有数据：大部落（如 #200JCGUVP）200 有数据；冷门部落可能 `cached=null` 或 `wars items=0`。
- 需要按 tag 精确调用；war 列表默认可能为空，加 `type=cwl` 或 `time[after]` 参数才有结果。

## 二、不可用（实测）

| 端点 | 状态 | 说明 |
|---|---|---|
| `/v2/server/1/bases` / 布局库 | **401** Authentication token missing | 需 UserToken/BotToken；ClashKing 明确拒绝本项目 |
| 官方 `api.clashofclans.com/v1/...` | **403** Missing authorization | 需开发者 key + **IP 白名单**（本项目所在地没有固定公网 IP）|
| `/v2/player/{tag}` 玩家档案 | 404 | 免费层没有实时玩家档案 |

## 三、替代方案（调研）

| 方案 | 可用性 | 成本/风险 | 结论 |
|---|---|---|---|
| 官方 API + 固定 IP 服务器 | 需申请 key 并把出口 IP 加白名单 | 需一台固定公网 IP 的服务器（本项目目前没有）；申请需审核 | 暂不可行 |
| 官方 API 代理（CaptEmulation/coc-api-proxy、ClashKingInc/ClashKingProxy）| 代理代码开源，但需自己提供 token | 仍需 key；公共实例不可信 | 不采用 |
| ClashKing 免费端点 | **已实测可用（上表）** | 无 token；覆盖率受收录限制 | **采用（已集成）** |
| ClashKing 静态数据 | **已实测可用** | 名称表 + 最高等级（TH19）| **采用（已集成）** |
| 社区静态数据仓库（Xayz-X/ClashOfClans 等）| 需人工核对版本 | 数据可能过期 | 仅作静态表校对 |
| 网页抓取 clashk.ing / clashofstats 等 | HTML/前端 JS，无稳定接口 | 不稳定且违反对方预期 | 不做 |

## 四、已集成到代码
- `clashlab/cocapi.py` 新增：`clan_cached`、`cached_members_th`、`clan_wars_filtered`、`static_names`、`static_max_level`
- `tools/ck_lookup.py` 查询 CLI：`--clan/--wars/--static/--player`
- 测试：`tests/test_cocapi_public.py` 3 项（mock HTTP）

## 五、对项目的意义
1. **战争成员 TH 不再依赖 OCR**：侦察时拿到敌方部落 tag → `clan_cached` 直接出成员 TH 表（有收录时）。
2. **TH 上限/静态数据**以 API 为准（TH19），本地表可自动校对。
3. 布局库仍不可得：敌方阵型结构依旧只能靠截图 + 标注（这条没有免费替代）。
