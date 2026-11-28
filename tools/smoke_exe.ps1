$env:CLASHLAB_SMOKE='1'
Get-ChildItem "$env:USERPROFILE\Downloads\ClashLab标注" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
$exe = (Get-Item 'dist_exe\ClashLabAnnotator.exe').FullName
$p = Start-Process -FilePath $exe -WorkingDirectory (Split-Path $exe) -PassThru
Start-Sleep -Seconds 8
Write-Output ('running=' + (-not $p.HasExited))
Get-ChildItem 'dist_exe\smoke_result.json' -ErrorAction SilentlyContinue | ForEach-Object { Get-Content $_.FullName -Raw }
Get-ChildItem "$env:USERPROFILE\Downloads\ClashLab标注" -ErrorAction SilentlyContinue | Select-Object Name,Length | Format-Table -AutoSize | Out-String -Width 80
if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force; Write-Output 'killed' }