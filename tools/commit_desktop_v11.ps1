& 'D:\Python313\python.exe' -u 'tools\package_desktop_v11.py'
$env:GH_TOKEN='GH_TOKEN_PLACEHOLDER'
$src='tools\upload_exe.py'
$dst='tools\upload_exe11.py'
(Get-Content $src -Raw -Encoding UTF8).Replace('Desktop_v1.0.exe','Desktop_v1.1.exe') | Set-Content $dst -Encoding UTF8
& 'D:\Python313\python.exe' -u 'tools\upload_exe11.py' 2>&1 | Select-Object -Last 5
& 'D:\Python313\python.exe' -u 'tools\sanitize_tokens.py'
$g = 'E:\Temp\mingit2\cmd\git.exe'
& $g add -A
& $g commit -m 'feat(desktop): v1.1 desktop UX (right-click delete, hover/cursor, coords+zoom readout, redo, shortcuts); no-python-required verified' 2>&1 | Select-Object -Last 2
& 'D:\Python313\python.exe' -u 'tools\push_changes.py' *> 'out\logs\push_exe11.log'
Write-Output ('push_exit=' + $LASTEXITCODE)