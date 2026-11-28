# 一条命令：新标注 -> 质检 -> 重训 -> 闸门 -> 打包 -> 上传
# 用法: $env:CLASHLAB_LABELS="a.json;b.json;..."; $env:CLASHLAB_VERSION="v2.0"; powershell -File tools/release_from_labels.ps1
$ErrorActionPreference = 'Continue'
$ver = $env:CLASHLAB_VERSION; if (-not $ver) { $ver = 'v2.0' }
$labels = ($env:CLASHLAB_LABELS -split ';') | Where-Object { $_.Trim() -ne '' }
if ($labels.Count -lt 1) { Write-Output 'NO_LABELS'; exit 1 }
Write-Output ('版本: ' + $ver + '  标注数: ' + $labels.Count)
Write-Output '=== 1) 质检 ==='
& 'D:/Python313/python.exe' -u 'tools/label_qa.py' --labels @labels | Tee-Object -FilePath 'out/logs/release_qa.log'
if ($LASTEXITCODE -ne 0) { Write-Output 'QA_FAILED'; exit 1 }
Write-Output '=== 2) 备份当前模型 ==='
$bak = 'models/_good_before_release'
if (Test-Path $bak) { Remove-Item $bak -Recurse -Force }
New-Item -ItemType Directory -Path $bak | Out-Null
Copy-Item 'models/hybrid_*' $bak
Write-Output '=== 3) 重训 ==='
$env:CLASHLAB_EXPORTS = ($labels -join [char]10)
& 'D:/Python313/python.exe' -u 'tools/train_hybrid_final.py' *> 'out/logs/release_train.log'
Write-Output ('train_exit=' + $LASTEXITCODE)
Remove-Item Env:/CLASHLAB_EXPORTS
if ($LASTEXITCODE -ne 0) { Copy-Item ($bak + '/hybrid_*') 'models/' -Force; Write-Output 'TRAIN_FAIL_RESTORE'; exit 1 }
Write-Output '=== 4) 导出 ONNX ==='
& 'D:/Python313/python.exe' -u 'tools/export_hybrid_onnx.py' *> 'out/logs/release_export.log'
Write-Output ('export_exit=' + $LASTEXITCODE)
Write-Output '=== 5) 质量闸门（b03 标准档 pred>=50）==='
$out = & 'D:/Python313/python.exe' -u 'tools/retest_preannotate.py' 2>&1
$out | Select-Object -Last 4 | Out-String -Width 150
$std = ($out | Select-String -Pattern '^standard').Line
if (-not ($std -match 'pred=(\d+)') -or [int]$matches[1] -lt 50) {
  Write-Output 'GATE_FAIL_RESTORE'
  Copy-Item ($bak + '/hybrid_*') 'models/' -Force
  & 'D:/Python313/python.exe' -u 'tools/export_hybrid_onnx.py' *> 'out/logs/release_export_restore.log'
  exit 1
}
Write-Output 'GATE_PASS'
Write-Output '=== 6) 重新打包 EXE ==='
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\build_v16.ps1 *> 'out/logs/release_build.log'
Write-Output ('build_exit=' + $LASTEXITCODE)
Write-Output '=== 7) 复制并上传 ==='
$dst = 'dist/ClashLabAnnotator_Desktop_' + $ver + '.exe'
Copy-Item 'dist_exe/ClashLabAnnotator.exe' $dst -Force
$md5 = (Get-FileHash $dst -Algorithm MD5).Hash
Write-Output ('EXE ' + (Get-Item $dst).Length + ' bytes md5 ' + $md5)
$up = Get-Content 'tools/upload_exe19.py' -Raw -Encoding UTF8
$up = $up.Replace('Desktop_v1.9.exe', ('Desktop_' + $ver + '.exe'))
Set-Content 'tools/_upload_release.py' $up -Encoding UTF8
$env:GH_TOKEN='GH_TOKEN_PLACEHOLDER'
& 'D:/Python313/python.exe' -u 'tools/_upload_release.py' *> 'out/logs/release_upload.log'
Write-Output ('upload_exit=' + $LASTEXITCODE)
Get-Content 'out/logs/release_upload.log' -Tail 4 | Out-String -Width 140