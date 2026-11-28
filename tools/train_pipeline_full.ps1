& 'D:\Python313\python.exe' -u 'tools\train_pipeline_full.py' *> 'out\logs\pipeline_full.log'
Write-Output ('exit=' + $LASTEXITCODE)
Get-Content 'out\logs\pipeline_full.log' -Tail 8 | Out-String -Width 140
Get-ChildItem 'models\pipeline_*' -ErrorAction SilentlyContinue | ForEach-Object { Write-Output ($_.Name + " " + $_.Length) }