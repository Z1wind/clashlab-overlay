$files = @()
for ($i=1; $i -le 8; $i++) { $files += (Join-Path $env:USERPROFILE ('Downloads\annot_b{0:D2}.json' -f $i)) }
& 'D:\Python313\python.exe' -u 'tools/train_pipeline_cv.py' --export ($files -join ',') --exclude '0,1' *> 'out\logs\pipeline.log'
Write-Output ('exit=' + $LASTEXITCODE)
Get-Content 'out\logs\pipeline.log' -Tail 12 | Out-String -Width 160