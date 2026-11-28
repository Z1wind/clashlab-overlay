$exe = (Get-Item 'dist_exe\ClashLabAnnotator.exe').FullName
$p = Start-Process -FilePath $exe -WorkingDirectory (Split-Path $exe) -PassThru
Start-Sleep -Seconds 10
$p.Refresh()
Write-Output ('title=' + $p.MainWindowTitle)
Write-Output ('handle=' + $p.MainWindowHandle)
Add-Type -AssemblyName System.Windows.Forms,System.Drawing
$b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($b.X, $b.Y, 0, 0, $bmp.Size)
$out = Join-Path (Get-Location) 'out\apk_qa\desktop_window.png'
$bmp.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()
Write-Output ('saved=' + (Test-Path $out))
& 'taskkill' /PID $p.Id /F 2>&1 | Select-Object -First 1