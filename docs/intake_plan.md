# 可延后整合行动表（由 `out/research/github_scan.md` §7 提炼）

> 来源：GitHub 调研 14 仓，只抄思路不 vendor 代码；每条标注改动文件·函数、预期收益、风险、
> 文件域冲突判定。**本表只排期，本轮不改任何 .py。**
> 冲突口径：目标文件当前被冻结/由其他线独占 → 标「待仲裁」；归属其他业务线但未冻结 → 不冲突，归该线排期。

| # | 改动文件 · 函数 | 抄什么（来源） | 预期收益 | 风险 | 文件域冲突判定 |
|---|---|---|---|---|---|
| 1 | `clashlab/overlay/runtime.py` · `_apply_mode_exstyle` | zaafar 基线缓存法（`Utils.cs:69-99`）：启动存基线 exStyle，仅 `IsClickable ^ WantClickable` 翻转时写回 | 消除读改写残留位导致的穿透态偶发失效 | 基线须在首次切模式前采集 | **待仲裁**：runtime.py 本轮输入修复刚冻结，禁改 |
| 2 | `clashlab/overlay/runtime.py` · `take_focus` | screen-masking `SW_SHOWNA`+全程 `SWP_NOACTIVATE`（`mask.go:58-59`），移除 `SetForegroundWindow` | PANEL 开关不抢雷电前台 | ImGui 键盘焦点需显式点击后再给 | **已落地，免做**：本轮 `take_focus` 已空实现、`_apply_mode_exstyle` 不调 SetForegroundWindow，仅保留自喂鼠标 |
| 3 | `clashlab/snap.py` · `_nms`（L56）+ `clashlab/template_match.py` · `scan`（L176） | Coc-Auto-Farm 同框双标 IoU>0.6 去重（`bot.py:45,484`），补中心距离 NMS 缺的 IoU 项 | 同一位置双标只计一次，类型误配减少 | 降阈值引入假阳性，需标注集复核 | 不冲突：归识别线（snap/template_match）排期 |
| 4 | `clashlab/template_match.py` · `scan`（L176，`min_score=0.60`） | Coc-Auto-Farm 分层阈值（`bot.py:463`）：主图高阈值，低对比小框夹 0.30–0.35 设 0.3 硬下限 | 低对比小框漏检减少，假阳性受控 | 需按候选尺寸/对比度分档，统计误配率 | 不冲突：归识别线排期 |
| 5 | `clashlab/snap.py` · `_template_conf`（L78）/ 分档（L145） | BuildABot UNKNOWN 兜底（`screen_detector.py:211-213`）：临界样本落 review/low 交人工，不硬归类型 | 错误类型计数下降，人工确认负担前移 | 需定义 margin 阈值，样本不足先保守 | 不冲突：归识别线排期 |
| 6 | `clashlab/touch.py` · `click_render_xy`（L442 通道注册） | Airtest TouchProxy 可插拔抽象（`android.py:96`）+ minitouch 长连接通道（README L104-184，生命周期 `minitouch.py:27-95`） | 消除 adb shell 往返，单击延迟向 socket 单程收敛（目标 <30ms，需实测） | 推二进制、Android 10+/模拟器兼容待验，先 dry-run | 不冲突：归触控线排期 |
| 7 | `clashlab/touch.py` · `swipe_render`（L578） | minitouch commit 批语义（`minitouch.c:593`；MaaTouch `InputThread.java:85-92`）：一批 per-contact 状态 + 一次 `c` 提交 | 手势原子化，减少中途丢点滑动跑偏 | 坐标须按握手头 `^ max-contacts max-x max-y max-pressure` 标定缩放 | 不冲突：归触控线排期 |
| 8 | `clashlab/sim.py` · `Simulator`（L66）/`score_spawn`（L101） | Hasty-CR 确定性 tick（`arena.py:58`、`engine.py:2991-3007` 先减后测、`engine.py:17-25` 阶段顺序）+ RoyaleSim 全整数（`fixed.rs:1-8`）+ DamageBuffer（`combat.rs:14-19`） | 攻击方案可离线回归评估，同图两跑一致 | CoC 数值不可搬，先跑通确定性再补物理；拍脑袋常数标待校准 | 不冲突：归策略线排期 |
| 9 | `clashlab/sim.py` · `top_spawns`（L193） | Hasty `legal_mask` 布尔掩码（`env.py:189-209`）：非法落点先滤再打分 | 评估函数不给非法落点虚高 | 需先定义 CoC 合法性规则 | 不冲突：归策略线排期 |
| 10 | `clashlab/planner.py` · 搜索升级（预研） | durak 四阶段 MCTS 骨架（`mcts.py:283-394`）+ 随机 rollout/W-N 基线（`mcts.py:359-379`） | 离线小局面验证「搜索 vs 启发式」收益 | 无剪枝无时间窗，只离线预研，不进主循环 | 不冲突：策略线预研，仅离线小局面 |

## 备注

- 反面教材不抄：Maknee `detection.py:154-164` 只取 max_val 定名（无 margin/二次确认/NMS，且 GPL-3.0），
  对应我们 snap「score 与类型打架」的同款病灶，勿回退全自动硬判。
- 顺序建议：6/7（触控收益最直接）→ 3/4/5（识别线并行）→ 8/9（策略离线）→ 1（待仲裁后）；
  10 为预研占位，不排主路径。
- 每条落地前先 dry-run/离线复跑，数字以实测为准，不沿用调研估算。
