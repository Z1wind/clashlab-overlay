& 'D:\Python313\python.exe' -u 'tools\patch_scanner_eval.py'
$files = @()
for ($i=1; $i -le 8; $i++) { $files += (Join-Path $env:USERPROFILE ('Downloads\annot_b{0:D2}.json' -f $i)) }
& 'D:\Python313\python.exe' -u 'tools/train_tile_scanner.py' --export ($files -join ',') --exclude '0,1' --epochs 32 --out 'models\tile_scanner_v2.pt' --report 'out\tile_scanner_report_v2.json' *> 'out\logs\tile_scanner2.log'
Write-Output ('exit=' + $LASTEXITCODE)
Get-Content 'out\logs\tile_scanner2.log' -Tail 10 | Out-String -Width 160