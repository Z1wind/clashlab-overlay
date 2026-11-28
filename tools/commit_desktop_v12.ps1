& 'D:\Python313\python.exe' -u 'tools\package_desktop_v12.py'
$env:GH_TOKEN='GH_TOKEN_PLACEHOLDER'
$src='tools\upload_exe11.py'
$dst='tools\upload_exe12.py'
(Get-Content $src -Raw -Encoding UTF8).Replace('Desktop_v1.1.exe','Desktop_v1.2.exe') | Set-Content $dst -Encoding UTF8
& 'D:\Python313\python.exe' -u 'tools\upload_exe12.py' 2>&1 | Select-Object -Last 5
& 'D:\Python313\python.exe' -u 'tools\sanitize_tokens.py'
$g = 'E:\Temp\mingit2\cmd\git.exe'
& $g add -A
& $g commit -m 'fix(desktop): click vs pan threshold (could not place points before); v1.2 EXE rebuilt + verified' 2>&1 | Select-Object -Last 2
& 'D:\Python313\python.exe' -u 'tools\push_changes.py' *> 'out\logs\push_exe12.log'
Write-Output ('push_exit=' + $LASTEXITCODE)