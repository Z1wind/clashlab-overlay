$ErrorActionPreference='Continue'
$root = (Get-Location).Path
& 'D:\Python313\python.exe' -u 'tools\fix_re_import.py'
& 'D:\Python313\python.exe' -u 'tools\build_desktop_html.py'
$html = Join-Path $root 'dist\ClashLabAnnotator_HTML_desktop.html'
$main = Join-Path $root 'tools\desktop_app.py'
$args = @(
 '--noconfirm','--onefile','--windowed','--name','ClashLabAnnotator',
 '--add-data',($html + ';.'),
 '--collect-all','webview','--collect-all','clr_loader','--collect-all','pythonnet',
 '--hidden-import','clr','--hidden-import','webview.platforms.edgechromium',
 '--distpath',(Join-Path $root 'dist_exe'),
 '--workpath',(Join-Path $root 'build_exe'),
 $main
)
& 'D:\Python313\python.exe' -m PyInstaller @args *> 'out\logs\pyinstaller_exe3.log'
Write-Output ('exit=' + $LASTEXITCODE)
Get-Content 'out\logs\pyinstaller_exe3.log' -Tail 5 | Out-String -Width 160
Get-ChildItem 'dist_exe\*.exe' -ErrorAction SilentlyContinue | ForEach-Object { Write-Output ($_.Name + " " + $_.Length) }