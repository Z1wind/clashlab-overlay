& 'D:\Python313\python.exe' -u 'tools\patch_pipeline_full_env.py'
# B 先重训最终流水线（8 张）
$exp = @(
 (Join-Path $env:USERPROFILE 'Downloads\annot_b01 (1).json'),
 (Join-Path $env:USERPROFILE 'Downloads\annot_b02 (1).json')
) + ((3..8 | ForEach-Object { Join-Path $env:USERPROFILE ('Downloads\annot_b{0:D2}.json' -f $_) }))
$env:CLASHLAB_EXPORTS = ($exp -join ';')
& 'D:\Python313\python.exe' -u 'tools/train_pipeline_full.py' *> 'out\logs\pipeline_full8.log'
Write-Output ('full_exit=' + $LASTEXITCODE)
Get-Content 'out\logs\pipeline_full8.log' -Tail 5 | Out-String -Width 140
Remove-Item Env:\CLASHLAB_EXPORTS