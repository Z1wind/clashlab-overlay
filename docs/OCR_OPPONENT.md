# 对手识别：截图 OCR → API 自动解析（默认强制最新数据）

链路：游戏截图 → 裁左上角 → RapidOCR（离线）→ 名字/部落 → ClashKing 公开 API search（fresh=True 强制回源）
→ 玩家 tag / TH / 部落 tag → 部落战双方成员 TH。

## 实测（用户提供的 998x559 对战截图）

`
[ocr] level='16.'  name='Mh Tipu'  clan='babY WaRioR'
[api] player=MH Tipu tag=#L0VUJ2U2P TH=15 | clan=baby warior #20R9PL0VU
[war] state=warEnded 20v20 双方成员 TH 列表（略）
`

- 玩家搜索返回 3 个同名候选，按「名字 + 部落名 + OCR 等级」打分后选中正确那个（TH15、部落 baby warior）
- OCR 大小写噪声（babY WaRioR）不影响匹配（fuzzy + 多查询变体）

## 数据必须最新——实现方式

1. `resolve_opponent(..., fresh=True)` 默认 fresh=True：`_get` 里 `if hit and not fresh` 直接绕过缓存回到源头
2. 结果带 `fetched_at` 时间戳；`cocapi.cache_age()` 可查缓存年龄
3. 部�战数据 TTL 30 秒、玩家搜索 TTL 120 秒；fresh 请求永远实时
4. 局限：ClashKing 是第三方聚合，极端情况比游戏内晚几秒；刚开打的战争可能显示上一场（warEnded），此时玩家 tag 的 TH 仍然有效

## 用法

`powershell
python tools\\ocr_opponent.py --image out\\ocr_test.png
python tools\\ocr_opponent.py --image shot.png --no-api
`

产物：`out/ocr_result.json`（OCR 原文 + API 解析 + fetched_at）

## 已知限制

- 只裁左上区域，游戏 UI 版本变化需调 `TOP_CROP`
- 等级徽章与 TH 可能差 1（OCR 16 / API 15），匹配按「±1 视为一致」
- 同名玩家多，需结合部落名 + 等级；极端重名可能要人工确认一次
