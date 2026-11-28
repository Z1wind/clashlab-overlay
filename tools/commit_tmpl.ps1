& 'D:\Python313\python.exe' -u 'tools\worklog_template.py'
& 'D:\Python313\python.exe' -u 'tools\sanitize_tokens.py'
$g = 'E:\Temp\mingit2\cmd\git.exe'
& $g add -A
& $g commit -m 'test(ml): user idea - key-texture template matching underperforms CNN (P0.29/R0.53 vs P0.715/R0.456); docs' 2>&1 | Select-Object -Last 1
$env:GH_TOKEN='GH_TOKEN_PLACEHOLDER'
& 'D:\Python313\python.exe' -u 'tools\push_changes.py' *> 'out\logs\push_tmpl.log'
Write-Output ('push_exit=' + $LASTEXITCODE)