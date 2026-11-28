$exe = (Get-Item 'dist_exe\ClashLabAnnotator.exe').FullName
# 保存桥 smoke
Get-ChildItem "$env:USERPROFILE\Downloads\ClashLab标注" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
$env:CLASHLAB_SMOKE='1'
$p = Start-Process -FilePath $exe -WorkingDirectory (Split-Path $exe) -PassThru
$null = $p.WaitForExit(60000)
Remove-Item Env:\CLASHLAB_SMOKE
Write-Output ('smoke_exit=' + $p.ExitCode)
Get-ChildItem 'dist_exe\smoke_result.json' -ErrorAction SilentlyContinue | ForEach-Object { Get-Content $_.FullName -Raw }
Get-ChildItem "$env:USERPROFILE\Downloads\ClashLab标注" -ErrorAction SilentlyContinue | Select-Object Name,Length | Format-Table -AutoSize | Out-String -Width 80
# 正常启动截图
$p2 = Start-Process -FilePath $exe -WorkingDirectory (Split-Path $exe) -PassThru
Start-Sleep -Seconds 12
Add-Type -AssemblyName System.Windows.Forms,System.Drawing
$b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($b.X, $b.Y, 0, 0, $bmp.Size)
$out = Join-Path (Get-Location) 'out\apk_qa\desktop_window2.png'
$bmp.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()
Write-Output ('screenshot=' + (Test-Path $out))
Get-Process ClashLabAnnotator -ErrorAction SilentlyContinue | Select-Object Id,MainWindowTitle | Format-Table -AutoSize | Out-String -Width 100
Get-Process ClashLabAnnotator -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue