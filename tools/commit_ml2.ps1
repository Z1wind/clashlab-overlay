& 'D:\Python313\python.exe' -u 'tools\docs_pipeline_append.py'
& 'D:\Python313\python.exe' -u 'tools\sanitize_tokens.py'
$g = 'E:\Temp\mingit2\cmd\git.exe'
& $g add -A
& $g commit -m 'feat(ml): classifier 91% CV; two-stage gate pipeline 71.5% prec/45.6% recall; docs updated' 2>&1 | Select-Object -Last 2
$env:GH_TOKEN='GH_TOKEN_PLACEHOLDER'
& 'D:\Python313\python.exe' -u 'tools\push_changes.py' *> 'out\logs\push_ml2.log'
Write-Output ('push_exit=' + $LASTEXITCODE)