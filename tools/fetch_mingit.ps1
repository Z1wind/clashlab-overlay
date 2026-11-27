$url = 'https://github.com/git-for-windows/git/releases/download/v2.47.1.windows.1/MinGit-2.47.1-64-bit.zip'
$dst = Join-Path $env:TEMP 'mingit.zip'
$dir = Join-Path $env:TEMP 'mingit2'
if (-not (Test-Path (Join-Path $dir 'cmd\git.exe'))) {
  Invoke-WebRequest -Uri $url -OutFile $dst -UseBasicParsing -TimeoutSec 300
  if (Test-Path $dir) { Remove-Item $dir -Recurse -Force -ErrorAction SilentlyContinue }
  Expand-Archive -Path $dst -DestinationPath $dir -Force
}
$g = Join-Path $dir 'cmd\git.exe'
Write-Output ("git: " + $g + " exists=" + (Test-Path $g))
& $g --version