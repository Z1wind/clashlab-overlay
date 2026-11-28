$ErrorActionPreference='Continue'
& 'D:\Python313\python.exe' -u 'tools\fix_title_patch.py'
& 'D:\Python313\python.exe' -u 'tools\build_desktop_html.py'
$args = @(
 '--noconfirm','--onefile','--windowed','--name','ClashLabAnnotator',
 '--add-data','dist\ClashLabAnnotator_HTML_desktop.html;.',
 '--collect-all','webview','--collect-all','clr_loader','--collect-all','pythonnet',
 '--hidden-import','clr','--hidden-import','webview.platforms.edgechromium',
 '--distpath','dist_exe','--workpath','build_exe','--specpath','build_exe',
 'tools\desktop_app.py'
)
& 'D:\Python313\python.exe' -m PyInstaller @args *> 'out\logs\pyinstaller_exe.log'
Write-Output ('exit=' + $LASTEXITCODE)
Get-Content 'out\logs\pyinstaller_exe.log' -Tail 4 | Out-String -Width 160
Get-ChildItem 'dist_exe\*.exe' -ErrorAction SilentlyContinue | ForEach-Object { Write-Output ($_.Name + " " + $_.Length) }