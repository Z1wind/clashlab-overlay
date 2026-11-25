# 打包与发布清单 / Packaging & Release

## 发布前自检

```powershell
python -m unittest discover -s tests
Get-ChildItem -Recurse -File -Include *.py,*.json,*.md | Select-String 'sk-[A-Za-z0-9]{12,}'   # 应为 0 条
Get-ChildItem -Recurse -File -Include *.py,*.json,*.md | Select-String 'C:\\Users\\'        # 应为 0 条
.\build_overlay.ps1
Start-Process .\dist\ClashOverlay.exe -ArgumentList '--seconds','6','--no-show' -Wait -PassThru | Select-Object ExitCode
```

## 入库范围

| 入库 | 内容 |
|---|---|
| 是 | `clashlab/` `tests/` `docs/` `assets/` `bases/` `config/` `layouts/`；`README*.md` `LICENSE` `ATTRIBUTIONS.md` `PACKAGING.md` `CHANGELOG.md` `requirements*.txt` |
| 否 | `out/` `dist/` `build*/` `scripts/` `_archive/` `dataset/`（运行时与构建产物，体积大，见 `.gitignore`）；`tools/` 只保留脚本 |

## 发布

- 资产：`ClashOverlay.exe`（约 90MB）、源码 zip、`SHA256SUMS.txt`。
- 上传：GitHub Release；本机访问不了 github.com 时可以用 API 脚本导入。
- 已验证：本地与远端的 md5 一致，Release 资产字节数一致。
