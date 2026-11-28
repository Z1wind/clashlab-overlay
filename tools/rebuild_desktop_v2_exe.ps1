$ErrorActionPreference='Continue'
& 'D:\Python313\python.exe' -u 'tools\switch_desktop_v2.py'
Get-Process ClashLabAnnotator -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Remove-Item 'dist_exe\ClashLabAnnotator.exe' -Force -ErrorAction SilentlyContinue
& 'D:\Python313\python.exe' -u 'tools\build_desktop_html.py' *> $null
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\build_exe3.ps1