& 'D:\Python313\python.exe' -u 'tools\fix_json_import.py'
& 'D:\Python313\python.exe' -u 'tools\train_pipeline_full.py' *> 'out\logs\pipeline_full2.log'
Write-Output ('exit=' + $LASTEXITCODE)
Get-Content 'out\logs\pipeline_full2.log' -Tail 6 | Out-String -Width 140
Get-ChildItem 'models\pipeline_*' -ErrorAction SilentlyContinue | ForEach-Object { Write-Output ($_.Name + " " + $_.Length) }