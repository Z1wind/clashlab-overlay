$ErrorActionPreference='Continue'
& 'D:\Python313\python.exe' -u 'tools\revert_train_convention.py'
$bak = 'models\_good_before_retrain'
if (Test-Path $bak) { Remove-Item $bak -Recurse -Force }
New-Item -ItemType Directory -Path $bak | Out-Null
Copy-Item 'models\hybrid_*' $bak
Remove-Item Env:\CLASHLAB_EXPORTS -ErrorAction SilentlyContinue
& 'D:\Python313\python.exe' -u 'tools\train_hybrid_full.py' *> 'out\logs\retrain_gated.log'
Write-Output ('train_exit=' + $LASTEXITCODE)
& 'D:\Python313\python.exe' -u 'tools\export_hybrid_onnx.py' 2>$null | Select-String -Pattern 'diff' | ForEach-Object { $_.Line }
$out = & 'D:\Python313\python.exe' -u 'tools\retest_preannotate.py' 2>&1
$out | Select-Object -Last 4 | Out-String -Width 150
$std = ($out | Select-String -Pattern '^standard').Line
Write-Output ('GATE_LINE=' + $std)
if ($std -match 'pred=(\d+)' -and [int]$matches[1] -ge 50) {
  Write-Output 'GATE_PASS'
} else {
  Write-Output 'GATE_FAIL_RESTORE'
  Copy-Item ($bak + '\hybrid_*') 'models\' -Force
}