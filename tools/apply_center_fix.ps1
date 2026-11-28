& 'D:\Python313\python.exe' -u 'tools\fix_center_convention.py'
& 'D:\Python313\python.exe' -m py_compile 'tools\train_hybrid_full.py' 'tools\preannotate_core.py'
Write-Output ('compile=' + $LASTEXITCODE)
& 'D:\Python313\python.exe' -u 'tools\check_pt_direct.py' 2>&1 | Select-Object -Last 4 | Out-String -Width 140