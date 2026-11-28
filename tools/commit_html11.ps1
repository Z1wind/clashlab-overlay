& 'D:\Python313\python.exe' -u 'tools\package_html11.py'
$env:GH_TOKEN='GH_TOKEN_PLACEHOLDER'
$src='tools\upload_html.py'
$dst='tools\upload_html11.py'
(Get-Content $src -Raw -Encoding UTF8).Replace('HTML_v1.0','HTML_v1.1') | Set-Content $dst -Encoding UTF8
& 'D:\Python313\python.exe' -u 'tools\upload_html11.py' 2>&1 | Select-Object -Last 5
& 'D:\Python313\python.exe' -u 'tools\sanitize_tokens.py'
$g = 'E:\Temp\mingit2\cmd\git.exe'
& $g add -A
& $g commit -m 'feat(html): v1.1 wheel zoom at cursor + left-drag pan + brighter grid; headless selftest' 2>&1 | Select-Object -Last 2
& 'D:\Python313\python.exe' -u 'tools\push_changes.py' *> 'out\logs\push_html11.log'
Write-Output ('push_exit=' + $LASTEXITCODE)