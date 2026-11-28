& 'D:\Python313\python.exe' -u 'tools\add_exclude.py'
$files = @()
for ($i=1; $i -le 8; $i++) { $files += (Join-Path $env:USERPROFILE ('Downloads\annot_b{0:D2}.json' -f $i)) }
& 'D:\Python313\python.exe' -u 'tools/train_real_aug.py' --export ($files -join ',') --epochs 26 --exclude-bases '0,1' --out 'models\apk_type_cls_aug6.pt' --report 'out\apk_type_report_aug6.json' *> 'out\logs\train_aug6.log'
Write-Output ('exit=' + $LASTEXITCODE)
Get-Content 'out\logs\train_aug6.log' | Select-String -Pattern 'skip|total|hold|CV mean|^  ' | ForEach-Object { $_.Line } | Select-Object -First 40