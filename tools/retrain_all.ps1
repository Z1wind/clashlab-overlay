$ErrorActionPreference='Continue'
$labels = @()
$labels += (Join-Path $env:USERPROFILE 'Downloads\annot_b01 (1).json')
$labels += (Join-Path $env:USERPROFILE 'Downloads\annot_b02 (1).json')
for ($i=3; $i -le 8; $i++) { $labels += (Join-Path $env:USERPROFILE ('Downloads\annot_b{0:D2}.json' -f $i)) }
Write-Output '=== 1) label QA ==='
& 'D:\Python313\python.exe' -u 'tools\label_qa.py' --labels @labels | Tee-Object -FilePath 'out\logs\retrain_qa.log'
if ($LASTEXITCODE -ne 0) { Write-Output 'QA_FAILED'; exit 1 }
Write-Output '=== 2) train hybrid full ==='
$env:CLASHLAB_EXPORTS = ($labels -join [char]10)
& 'D:\Python313\python.exe' -u 'tools\train_hybrid_full.py' *> 'out\logs\retrain_train.log'
Write-Output ('train_exit=' + $LASTEXITCODE)
Remove-Item Env:\CLASHLAB_EXPORTS
Get-Content 'out\logs\retrain_train.log' -Tail 4 | Out-String -Width 140
Write-Output '=== 3) export onnx ==='
& 'D:\Python313\python.exe' -u 'tools\export_hybrid_onnx.py' 2>$null | Select-String -Pattern 'exported|diff|hybrid_' | ForEach-Object { $_.Line }