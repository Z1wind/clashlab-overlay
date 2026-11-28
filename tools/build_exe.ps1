$ErrorActionPreference='Continue'
$args = @(
 '--noconfirm','--onefile','--windowed','--name','ClashLab标注器',
 '--add-data','dist\ClashLabAnnotator_HTML_desktop.html;.',
 '--collect-all','webview','--collect-all','clr_loader','--collect-all','pythonnet',
 '--hidden-import','clr','--hidden-import','webview.platforms.edgechromium',
 '--distpath','dist_exe','--workpath','build_exe','--specpath','build_exe',
 'tools\desktop_app.py'
)
& 'D:\Python313\python.exe' -m PyInstaller @args *> 'out\logs\pyinstaller_exe.log'
Write-Output ('exit=' + $LASTEXITCODE)
Get-Content 'out\logs\pyinstaller_exe.log' -Tail 6 | Out-String -Width 160