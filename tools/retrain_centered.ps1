$ErrorActionPreference='Continue'
Remove-Item Env:\CLASHLAB_EXPORTS -ErrorAction SilentlyContinue
& 'D:\Python313\python.exe' -u 'tools\train_hybrid_full.py' *> 'out\logs\retrain_centered.log'
Write-Output ('train_exit=' + $LASTEXITCODE)
& 'D:\Python313\python.exe' -u 'tools\export_hybrid_onnx.py' 2>$null | Select-String -Pattern 'diff' | ForEach-Object { $_.Line }
& 'D:\Python313\python.exe' -u 'tools\retest_preannotate.py' 2>&1 | Select-Object -Last 4 | Out-String -Width 150