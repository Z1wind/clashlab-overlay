Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.StartTime -lt (Get-Date).AddMinutes(-10) } | Stop-Process -Force -ErrorAction SilentlyContinue
$pick = @('b01 (1)','b02 (1)','b03','b05','b08','b10','b14','b20')
$labels = @()
foreach ($n in $pick) { $labels += (Join-Path $env:USERPROFILE ('Downloads\annot_' + $n + '.json')) }
Write-Output ('subset=' + $labels.Count)
$env:CLASHLAB_EXPORTS = ($labels -join [char]10)
& 'D:/Python313/python.exe' -u 'tools/train_hybrid_cv.py' *> 'out/logs/hybrid_subset_cv.log'
Write-Output ('cv_exit=' + $LASTEXITCODE)
Remove-Item Env:/CLASHLAB_EXPORTS
Get-Content 'out/logs/hybrid_subset_cv.log' -Tail 10 | Out-String -Width 170