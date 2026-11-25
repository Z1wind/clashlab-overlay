# base link 解码调研 / Base-link decoding research

> 结论先行：**目前没有公开可行的离线解码方案**，社区项目也都把链接当作不透明 token。
> Verdict: no public offline decoder exists; community projects treat the link as an opaque token.

## 我们实测到的链接结构 / Observed structure

`https://link.clashofclans.com/<lang>?action=OpenLayout&id=TH<等级>:<HV|WB>:<base64url>`

- payload 只有 **24 字节**：`u32BE 声明长度(16) + u32BE kind(2) + 16B 不透明值`；
- 24B 装不下 44×44 网格与 100+ 建筑，压缩也不可能；
- 落地页（Next.js）只有 `clashofclans://` 深链，没有 tile 数据。

## 公开实现核查 / Public implementations checked

| 来源 | 结果 |
|---|---|
| [Peter537/clash-of-clans-base-validator](https://github.com/Peter537/clash-of-clans-base-validator)（MIT）`docs/sources.md` | payload 明确视为 opaque，社区无 codec |
| [Wire15/clash-buddy](https://github.com/Wire15/clash-buddy) `content/layouts/th16.json` | 19 条记录只有 `copyLink` + `imageUrl`，无坐标 |
| [rudrolab/baselinkhub](https://github.com/rudrolab/baselinkhub) `js/app.js` | 链接目录站，base64 仅用于用户上传图片 |
| [sqggde/coctimer](https://github.com/sqggde/coctimer) `js/bases.js` | 只从链接里解析 TH 等级 |
| [rishi-ragavan/Viking--Clash_of_Clans_base-optimizer](https://github.com/rishi-ragavan/Viking--Clash_of_Clans_base-optimizer) | 抓 cocbases.com 图片；`generate_layout_json.py` 注释写明真实 tile 坐标暂时留空，他们同样靠 YOLO 检测 |
| [laurentDellaNegra/coc-layout-ai](https://github.com/laurentDellaNegra/coc-layout-ai) | 纯 3D 布局编辑器，无真实基地导入 |
| [clashofclans-layouts.com](https://clashofclans-layouts.com/) / [cocbases.com](https://cocbases.com/) | 页面只提供图片 + 复制链接，无坐标 JSON/API |

## 可行的替代路径 / Feasible alternatives

1. **游戏内导入 + 截图（推荐）**：在雷电模拟器里点开分享链接 → 游戏加载阵型 → 我们截屏 + 44×44 标定 → 走现有标注/检测。解码发生在游戏客户端内，不需要我们破解。
2. **半自动标注工具**：`tools/annotate/`，预填 + 点选修正，十分钟内可标一阵。
3. **图片数据集扩容**：cocbases.com / clashofclans-layouts.com 有大量阵型图，可扩充训练集（仍需人工/半自动标注）。

## 已实现 / Implemented

- `clashlab/baselink.py`：严格链接解析、24B 信封诊断、可插拔 codec 链（未来若出现自包含格式可直接接入）；
- `tools/baselink_probe.py`：对 `bases/th16/*/source.json` 的 5 条真实链接做诊断；
- 30 项单元测试。
