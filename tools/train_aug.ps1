$files = @()
for ($i=1; $i -le 8; $i++) { $files += (Join-Path $env:USERPROFILE ('Downloads\annot_b{0:D2}.json' -f $i)) }
& 'D:\Python313\python.exe' -u 'tools\train_real_aug.py' --export ($files -join ',') --epochs 26 *> 'out\logs\train_aug.log'
Write-Output ('exit=' + $LASTEXITCODE)
Get-Content 'out\logs\train_aug.log' -Tail 30 | Out-String -Width 160