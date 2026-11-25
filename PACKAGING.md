# 打包与发布清单 / Packaging & Release

## 发布前自检 / Pre-release checks

```powershell
python -m unittest discover -s tests                      # 86 tests
Get-ChildItem -Recurse -File -Include *.py,*.json,*.md | Select-String 'sk-[A-Za-z0-9]{12,}'   # 0 hits
Get-ChildItem -Recurse -File -Include *.py,*.json,*.md | Select-String 'C:\\Users\\'        # 0 hits
.\build_overlay.ps1
Start-Process .\dist\ClashOverlay.exe -ArgumentList '--seconds','6','--no-show' -Wait -PassThru | Select-Object ExitCode
```

## 入库范围 / Tracked in git

| 入 / In | 说明 |
|---|---|
| `clashlab/` `tests/` `docs/` `assets/` `bases/` `config/` `layouts/` | 代码/测试/文档/素材/阵型 |
| `README*.md` `LICENSE` `ATTRIBUTIONS.md` `PACKAGING.md` `CHANGELOG.md` `requirements*.txt` | 说明与依赖 |
| ❌ `out/` `dist/` `build*/` `scripts/` `_archive/` `dataset/` | 运行时/构建产物（体积大，见 .gitignore） |
| ❌ `tools/` 实验产物 | 仅保留脚本 |

## 发布 / Release

- 资产：`ClashOverlay.exe`（约 90MB）、源码 zip、`SHA256SUMS.txt`；
- 上传：GitHub Release（若本机 github.com 不可达，可用 API 脚本导入）；
- 已验证：本地与远端 md5 一致、Release 资产字节数一致。
