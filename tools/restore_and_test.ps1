& 'D:\Python313\python.exe' -u 'tools\restore_good_models.py'
& 'D:\Python313\python.exe' -u 'tools\retest_preannotate.py' 2>&1 | Select-Object -Last 4 | Out-String -Width 150