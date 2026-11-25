# tests/ —— 纯离线 unittest（不起覆盖层 / 不起 EXE / 不碰 adb / 不弹窗）

本目录只**新增**测试文件，**绝不修改 `clashlab\**`**（另一代码线正在改 overlay/pages.py、
tactics.py、runtime.py）。所有被测数据一律用 `tempfile` 临时目录构造，真实
`out\overlay\tactics\plan.json`、`knowledge\tactics\` 只读不写。

## 被测版本快照（测试针对该版本代码；他人继续改文件后哈希会变，需重录）

| 文件 | mtime | sha256 |
| --- | --- | --- |
| `clashlab\overlay\tactics.py` | 2026-11-24 14:35:09 | `758F854B73F3A8441333DA54A12BD0EE1FCCA1EF36035751F4284FE4EADBA6CC` |
| `clashlab\overlay\pages.py` | 2026-11-24 14:22:23 | `C227F5D05C46EC89007B2747953096AC1EE84CD894D2BE9698909073DA57BF06` |
| `clashlab\knowledge.py` | 2026-11-24 13:39:31 | `1BF3745AD70FDE02501E24E2DEA61F78061AD5A73B7BD9ECA06B357971AA78BE` |

> pages.py 仅做版本记录，本批测试不 import 它（无显示环境下 ImGui/glfw 会崩）。

## 覆盖范围

1. `test_tactics_parse.py` —— `tactics.parse_plan_marks` 正/负用例（全角括号逗号、
   `tile(36,9)` 无「格」字、裸 `鹰炮(0,9)`、小数 `格(36.0,9.0)` 过；方括号、
   无标签裸坐标、越界、绕开区、缺三段标题拒）。
2. `test_fallback.py` —— 三段式标题 + 自带合法 `格(x,y)` 兜底文本可被解析、坐标正确。
3. `test_plan_atomic.py` —— `.tmp` 残留 / 旧版完整目标并存时 `load_plan` 只拿完整或旧版，
   不抛解析异常；`_atomic_write_json` 成功路径。
4. `test_cache.py` —— `knowledge.load_cards` / `tactics.load_local` 的 mtime 缓存：
   同 mtime 命中（同对象），改 mtime 必失效重读。
5. `test_perf_baseline.py` —— `load_local` <5ms、`parse_plan_marks` <5ms、`retrieve` <50ms；
   超阈值只记录数字、不判死。

## 运行

```
D:\Python313\python.exe -m unittest discover -s tests -v
```
