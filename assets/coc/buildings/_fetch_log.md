# 建筑素材库抓取过程记录（_fetch_log.md）

生成时间：2026-11-23（Asia/Shanghai）。记录对象：`assets/coc/buildings/` 下全部素材与 `manifest_buildings.json`。

## 1. 来源白名单与可达性实测（每源 3 次重试，间隔 3s/6s/12s）

| 来源 | 结果 | 说明 |
|---|---|---|
| clashofclans.fandom.com（CoC Wiki 页面/API） | 不可达 | DNS 解析落到 128.242.245.212（污染/黑洞），连接超时；HTTP 80 同样超时 |
| static.wikia.nocookie.net（Fandom CDN 主机） | 主机可达 | 任意路径返回 404，说明 TCP/TLS 通，但无有效文件路径可构造（目录哈希未知） |
| Supercell 官方站 supercell.com | 可达 | 仅营销横幅，无分级建筑 sprite；Fan Kit 无建筑图 |
| coc.wiki | 不可达 | DNS 解析失败（域名不存在/被拦截） |
| allorigins / corsproxy / codetabs 代理 | 不可达 | 超时 / 403，无法借代理取 Fandom 页面 |
| npm registry / jsdelivr / unpkg（公开开源镜像） | 可达 | 用于补缺 storage/collector，溯源见 §4 |
| github.com 直连 | 拒绝连接 | jsdelivr `gh` 镜像无可用公开 CoC 素材仓库（Bing 未给出候选） |

网络间歇离线：个别请求出现 SSL handshake timeout，重试后成功；3 次仍失败的命令按规则追加到 `out/snap/_offline.log`（该文件含其他任务的历史记录，本任务未改写）。

## 2. 既有批次（203 张，17 个 kebab 目录）

- 未重新下载、未移动、未改名（路径被其他代码引用）。
- 来源无法确认：`source_url="unknown (pre-existing batch)"`、`fetched_at="unknown"`，**未编造 URL/时间**。
- 目录→统一 type 映射：air-defense→airdef、eagle-artillery→eagle、scattershot→scatter、inferno-tower→inferno、x-bow→xbow、wizard-tower→wiztower、cannon→cannon、archer-tower→archertower、mortar→mortar、air-sweeper→sweeper、town-hall→townhall、bomb-tower→bombtower、hidden-tesla→tesla、spell-tower→spelltower、multi-archer-tower→multiarcher、firespitter→firespitter、monolith→monolith。
- 等级号取自文件名 `level-N.png`（`level_source: "filename"`）；w_tiles/h_tiles 按家乡标准占地记录（防御 3×3、大本营 4×4），非像素测量。
- 自检：203 张均有 alpha 通道（>5%）；唯一尺寸偏差：`scattershot/level-7.png` 125×121（长边 <128），属既有批次，未改动，在此登记。

## 3. 补缺 storage / collector（16 张，真实 URL + 抓取时间）

直链规律（jsdelivr 固定版本）：
`https://cdn.jsdelivr.net/npm/clash-of-clans-data@0.19.1/images/home/resource-buildings/{pkg_dir}/normal/level-{n}.png`

- 溯源：该 npm 包 README 明确「All game data is sourced from the Clash of Clans Wiki (Fandom)」，包 MIT 许可；游戏资产 © Supercell，按 Fan Content Policy 仅本地非商业使用。
- 校验：alpha>5%、主体外接框合理、长边≥128（过小则 LANCZOS 放大并记录 `upscaled`）；抓取后已裁掉透明边距（`recropped`）。

| 文件 | 变体 | 等级 | 源文件 |
|---|---|---|---|
| storage_gold_l1/l7/l13.png | gold | 1/7/13 | gold-storage/normal/level-1/7/13.png |
| storage_elixir_l7/l13.png | elixir | 7/13 | elixir-storage/normal/level-7/13.png |
| storage_dark_l1/l6.png | dark | 1/6 | dark-elixir-storage/normal/level-1/6.png |
| collector_gold_l1/l7/l12.png | gold | 1/7/12 | gold-mine/normal/level-1/7/12.png |
| collector_elixir_l1/l7/l13.png | elixir | 1/7/13 | elixir-collector/normal/level-1/7/13.png |
| collector_dark_l1/l7.png | dark | 1/7 | dark-elixir-drill/normal/level-1/7.png |

弃用/重试记录（不合规未入库）：
- `storage_elixir_l1.png`：alpha 0.042<0.05 → 改抓 l2，l2 主体过小（bbox 0.122）→ 经裁边后入库（l7/l13 保留）。
- `collector_gold_l13.png`：bbox 0.92 贴边 → 改抓 l12。
- `collector_dark_l8.png`：bbox 0.95 贴边 → 改抓 l7。

## 4. wall（城墙）三条尝试路径

1. jsdelivr GitHub 镜像找公开 CoC 素材仓库：Bing 未返回可用候选，直探仓库 404 → 失败。
2. npm 包内检索：`clash-of-clans-data@0.19.1` 仅含 builder（夜世界）城墙图，无家乡城墙 → 失败。
3. **自有截图派生（采用）**：从 `out/snap/_source/home_village.png`（自持有游戏截图，TH13 金色城墙可见）切出约 3–4 块连排墙，存 `wall/wall_l14_strip.png`（288→336×144，LANCZOS 放大）。`bg: "screenshot-derived"`、`kind: "wall_strip"`、`source_url: "derived from own screenshot (out/snap/_source/home_village.png); no external fetch"`、`license: self-owned in-game screenshot, local non-commercial use`。说明：等距视角下墙面为斜线，切片保留草地底、无 alpha；本地仅取得 l14 金色一档，其他等级档无来源。

## 5. 失败来源汇总

- Fandom 全站（页面/API/CDN 有效路径）：DNS 污染 + 超时，3 次重试均失败。
- coc.wiki：DNS 失败。
- 通用 CORS 代理：超时/403。
- github.com 直连：拒绝连接。

## 6. 最终缺项

`stats.missing = []`（20 类全部覆盖）。已知局限（非缺项）：
- wall 仅 l14 一档，无低等级档；
- storage/collector 的 dark 变体只各有 1–2 档；
- 既有 203 张来源不明，仅可作本地比对参考，不可对外分发。

## 7. 许可与使用声明

全部素材仅用于本地非商业模板比对；游戏内容 © Supercell，遵循 Supercell Fan Content Policy（https://supercell.com/en/fan-content-policy/），不打包进任何对外分发版。
