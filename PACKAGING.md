# 开源打包清单（发布前逐项核对）

## 1. 入库范围

| 目录/文件 | 入库 | 说明 |
|---|---|---|
| `clashlab/` `tools/` `tests/` `layouts/` `docs/` | ✅ | 核心代码/脚本/测试/示例 |
| `bases/th16/{01..06}/` | ✅（可选） | 约 16.7MB（base.png + layout.json）；若仓库要轻量，改为 release 附件 |
| `assets/coc/` | ✅ | 约 10.8MB 建筑素材 |
| `config/` | ✅ | 标定/锚点配置，确认无本机绝对路径 |
| `run_overlay.py` `overlay_exe_main.py` `build_overlay.ps1` `ClashOverlay.spec` | ✅ | 入口与打包 |
| `out/` | ❌ | 运行时产物，已进 .gitignore |
| `dist/` | ❌ | exe 走 GitHub Release，不入库 |
| `*.bak_*` `项目导出_*.zip` | ❌ | 临时/备份 |
| `.dsh/` | ❌ | 本机会话目录 |

## 2. 发布前自检（必须全部真实执行）

```powershell
# ① 测试全绿
python -m unittest discover -s tests

# ② 密钥扫描：不得出现 sk- 明文
Get-ChildItem -Recurse -File -Include *.py,*.json,*.md,*.ps1,*.txt | Select-String 'sk-[A-Za-z0-9]{12,}'

# ③ 绝对路径扫描：不得出现本机用户名路径
Get-ChildItem -Recurse -File -Include *.py,*.json,*.md | Select-String 'C:\\Users\\'

# ④ 打包并自检
.\build_overlay.ps1
Start-Process .\dist\ClashOverlay.exe -ArgumentList '--seconds','6','--no-show' -Wait -PassThru | Select-Object ExitCode
```

## 3. 体积与附件策略

- 仓库本体目标 < 40MB（代码 3.9MB + 素材 10.8MB + 六阵 16.7MB + 文档）；
- `dist/ClashOverlay.exe`（约 90MB）作为 **Release asset** 上传，附 sha256；
- `out/` 中的证据图（截图/叠加图）挑选 ≤10 张放入 `docs/screenshots/`，其余不入库。

## 4. 许可证与署名

- [ ] 作者确认主许可证（建议 MIT）并放 `LICENSE`；
- [ ] README「许可证与第三方」保留：clash-blueprint-engine (MIT)、base-validator (MIT)、ClashKingAssets、Supercell Fan Content Policy；
- [ ] 若移植了 analyzer 指标，README/源码注释注明来源与 MIT 许可。

## 5. 发布流程

1. 本机跑完第 2 节四项自检；
2. `git init && git add . && git commit -m "chore: initial open-source release"`；
3. 打 tag（如 `v0.1.0`）；
4. GitHub 建 Release，上传 `ClashOverlay.exe` + `sha256.txt`；
5. README 顶部补 Release 下载链接与快速开始三项命令。
