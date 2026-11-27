# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
def c(s): return BT + s + BT
lines = [
 "",
 "## 2026-11-27 A/B/C 批次",
 "",
 "### A 内置标注器服务（完成并实机验证）",
 "- " + c("clashlab/annotator.py") + " 幂等 start_server/is_running/ensure_running/stop_server；tools/annotate_web.py 变薄 CLI 并保留 serve/STATE 兼容",
 "- 面板设置页「启动标注器」按钮：实机点击后日志出现 annotator started，HTTP 200（9,542 bytes）",
 "- 无渲染目标时 PANEL 独立显示（主屏右侧 440x700）",
 "",
 "### B 自动候选（接口已接，质量不达标 -> 仅实验）",
 "- " + c("clashlab/auto_candidates.py") + "：分类器滑窗候选 + 背景平坦度过滤 + 去重；" + c("/candidates") + " 路由 + 页面「自动候选」按钮",
 "- 实测（enemy_scout_live）：原始候选 1,465 -> 去重后 30，但分类器退化（几乎全是 gold-mine conf=1.0），不能用于生产",
 "- 结论：B 只保留实验按钮并在页面标注「实验候选」；要可用必须先补真实建筑负样本训练（见 docs/C_DETECT_SPIKE.md）",
 "",
 "### C 模拟升级（完成）",
 "- units.py 新增 HERO_STATS（5 英雄 dps/hp/能力）与 SPELL_EFFECTS（9 法术修正）",
 "- battle_sim.simulate 扩展：spells/th/heroes/cc_dps，输出 modifiers（th_scale/spells/heroes/cc_dps/wall_cost）",
 "- sim_attack --compare：ground/air/hybrid 三配比对比（06 阵实测：ground 3星 95% 6.2s，air 3星 98% 5.5s，hybrid 3星 88% 6.3s）",
 "- 测试：sim_upgrade 3 项通过；全量 350 OK",
]
p = os.path.join(BASE, "docs", "STATUS.md")
t = open(p, encoding="utf-8").read()
if "A/B/C 批次" not in t:
    open(p, "w", encoding="utf-8", newline="\n").write(t.rstrip() + "\n" + "\n".join(lines) + "\n")
    print("STATUS updated")
