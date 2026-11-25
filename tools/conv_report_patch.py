# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
p = os.path.join(BASE, "out", "tactics", "_convention", "convention_report.md")
add = "\n## 2026-11-25 修订（外部 base-validator 交叉验证后）\n\n1. **口径B 偶数尺寸缺陷（已修 check_convention.py 的 cells_B）**：旧实现 range(-r, r+1) 在 k 为偶数时只盖 1 格（2×2 少一行），导致口径B 贴边数少报 4 条。\n   - 修前合计：A=52 / B=46 / C=34 / 皆=24\n   - 修后合计：A=51 / B=50 / C=32 / 皆=24\n   - 其中 B 46→50 与上游 base-validator 口径B（真实足迹）=50 完全一致。\n2. **spell-tower 尺寸 3×3 → 2×2**（assets.py STATS 与 check_convention.py FOOTPRINT 同步修改）：\n   - 证据：上游 ruleset home-2026-11-17（status=reviewed）判 2×2；其 art manifest 由真实精灵包围盒量得 width_tiles=1.994。两处独立证据一致。\n   - 影响：口径C 越界 34→32（02 由 13→12、04 由 3→2）；口径A 52→51。\n   - 上游转换器 tools/cv_to_validator.py 里我方尺寸表（OUR_FOOTPRINT）原为硬编码副本，本次一并改为从 assets.py STATS 自动同步，避免两份表再次漂移。\n3. **未采纳的分歧**：上游 ruleset 判 eagle-artillery=4×4，我方维持 3×3 —— 上游 art manifest 中没有 eagle（其美术目录已换成 multi_gear_tower / firecracker），4×4 无精灵证据；且若改 4×4 会在 05 阵凭空多出一处与 inferno 的重叠。待第三方（wiki / 游戏内实际占地）核证后再定。\n4. **firespitter 归属**：我方 assets.py 自注「TH17 建筑（2024-11-25 加入），TH16 不可建造」，上游在 TH16 profile 下也判不可用 —— 说明 03/04/05 这些阵很可能不是 TH16（是 TH17 阵或标签误写），需按截图确认后再改数据。"
open(p, "a", encoding="utf-8").write(add)
print("appended", len(add), "chars")
