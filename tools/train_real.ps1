$env:PYTHONIOENCODING='utf-8'
$files = @()
for ($i=1; $i -le 8; $i++) { $files += (Join-Path $env:USERPROFILE ('Downloads\annot_b{0:D2}.json' -f $i)) }
$joined = ($files -join ',')
& 'D:\Python313\python.exe' -u 'tools\train_from_apk_export.py' --export $joined --epochs 14 --out 'models\apk_type_cls_real.pt' --report 'out\apk_type_report_real.json' *> 'out\logs\train_real.log'
Write-Output ('exit=' + $LASTEXITCODE)
Get-Content 'out\logs\train_real.log' -Tail 20 | Out-String -Width 160