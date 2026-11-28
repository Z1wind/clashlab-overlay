& 'D:\Python313\python.exe' -u 'tools\add_size_arg.py'
& 'D:\Python313\python.exe' -u 'tools\sweep_classifier.py' *> 'out\logs\sweep.log'
Write-Output ('exit=' + $LASTEXITCODE)
Get-Content 'out\logs\sweep.log' -Tail 25 | Out-String -Width 150