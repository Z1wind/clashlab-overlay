& 'D:\Python313\python.exe' -u 'tools\patch_precise_a.py'
& 'D:\Python313\python.exe' -m py_compile 'tools\desktop_app.py'
Write-Output ('compile=' + $LASTEXITCODE)
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\build_v16.ps1