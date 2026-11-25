# 实机多轮测试报告（soak）

运行方式：逐轮启动覆盖层/EXE，真实截图，检查退出码、日志 Traceback、runtime end、截图字节数。

| 轮次 | 模式 | 布局 | 退出码 | 日志行 | Traceback | 截图 | 结果 |
|---|---|---|---|---|---|---|---|
| r1_hud_nolayout | HUD | 无 | 0 | 39 | 0 | 2329642 B | PASS |
| r2_hud_layout | HUD | 有 | 0 | 39 | 0 | 2884457 B | PASS |
| r3_panel_layout | PANEL | 有 | 0 | 49 | 0 | 2571623 B | PASS |
| r4_panel_nolayout | PANEL | 无 | 0 | 49 | 0 | 2553967 B | PASS |
| r5_hud_resize | HUD+中途改窗口 | 有 | 0 | 60 | 0 | 2882369 B | PASS |
| r6_exe_selfcheck | EXE 自检 | - | 0 | - | 0 | - | PASS |
| r7_exe_hud | EXE HUD | 有 | 0 | - | 0 | 1716436 B | PASS |

## 结论

- 本轮 **7/7 通过**；所有运行的退出码均为 0、日志 0 条 Traceback、截图非空。
- 中途改窗口大小（-20% 再还原）触发自动重标定，无崩溃。
- EXE 自检 ExitCode=0；EXE HUD 实机运行截图 1,716,436 B。
- 说明：本报告只证明「在这些场景下不崩溃、行为符合预期」，**不等于零 bug**；已知限制见 README「已知限制」。