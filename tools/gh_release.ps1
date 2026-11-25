param(
  [Parameter(Mandatory=$true)][string]$Token,
  [string]$Owner = 'Z1wind',
  [string]$Repo = 'clashlab-overlay'
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
Add-Type -AssemblyName System.Net.Http
$client = New-Object System.Net.Http.HttpClient
$client.Timeout = [TimeSpan]::FromMinutes(20)
$client.DefaultRequestHeaders.Add('User-Agent', 'clashlab-release')
$client.DefaultRequestHeaders.Add('Authorization', ('token ' + $Token))
$client.DefaultRequestHeaders.Add('Accept', 'application/vnd.github+json')
$api = 'https://api.github.com'

function Send([string]$method, [string]$url, $obj) {
  $req = New-Object System.Net.Http.HttpRequestMessage([System.Net.Http.HttpMethod]::new($method), $url)
  if ($null -ne $obj) {
    $json = $obj | ConvertTo-Json -Depth 20 -Compress
    $req.Content = New-Object System.Net.Http.StringContent($json, [Text.Encoding]::UTF8, 'application/json')
  }
  $resp = $client.SendAsync($req).GetAwaiter().GetResult()
  $text = $resp.Content.ReadAsStringAsync().GetAwaiter().GetResult()
  if (-not $resp.IsSuccessStatusCode) { throw ('HTTP ' + [int]$resp.StatusCode + ' ' + $url + ' :: ' + $text.Substring(0, [Math]::Min(300, $text.Length))) }
  return ($text | ConvertFrom-Json)
}

# 元数据：描述 / 主页 / topics
try {
  $meta = @{ description = 'An LLM-assisted Clash of Clans base-layout research tool: scout → 44x44 calibration → defense score → weak points → tactical diagram. Open source (MIT), out-of-process overlay over LDPlayer.'; homepage = 'https://github.com/Z1wind/clashlab-overlay'; topics = @('clash-of-clans','overlay','imgui','computer-vision','layout-analysis','llm','research-tool','python','mit-license') }
  $r = Send 'PATCH' ($api + '/repos/' + $Owner + '/' + $Repo) $meta
  Write-Output ('meta updated: ' + $r.full_name)
} catch { Write-Output ('meta failed: ' + $_.Exception.Message) }

# Release
$body = @{ tag_name = 'v0.1.0'; name = 'ClashLab v0.1.0 - LLM-assisted layout research tool'; draft = $false; prerelease = $false; body = ('First open-source release.' + [Environment]::NewLine + [Environment]::NewLine + '- Out-of-process ImGui overlay (HUD/PANEL), zero injection' + [Environment]::NewLine + '- Defense score 0-100 with S-F grade and located weak points' + [Environment]::NewLine + '- Giant-arrow tactical diagram and 2D simulation in panel' + [Environment]::NewLine + '- 86 unit tests, MIT license' + [Environment]::NewLine + [Environment]::NewLine + 'Assets: ClashOverlay.exe (Windows x64) and source zip; verify with SHA256SUMS.txt.') }
try { $rel = Send 'POST' ($api + '/repos/' + $Owner + '/' + $Repo + '/releases') $body; Write-Output ('release: ' + $rel.tag_name + ' id=' + $rel.id) } catch { Write-Output ('release failed: ' + $_.Exception.Message); exit 1 }

$uploadBase = ([string]$rel.upload_url) -replace '\{\?name,label\}', ''
foreach ($f in @('ClashOverlay.exe', 'ClashLab_open_source_v0.1.0.zip', 'SHA256SUMS.txt')) {
  $p = Join-Path $root ('out\release\' + $f)
  if (-not (Test-Path $p)) { Write-Output ('SKIP missing ' + $f); continue }
  $bytes = [IO.File]::ReadAllBytes($p)
  $content = New-Object System.Net.Http.ByteArrayContent($bytes)
  $content.Headers.Add('Content-Type', 'application/octet-stream')
  $url = $uploadBase + '?name=' + [uri]::EscapeDataString($f)
  $req = New-Object System.Net.Http.HttpRequestMessage([System.Net.Http.HttpMethod]::Post, $url)
  $req.Content = $content
  $resp = $client.SendAsync($req).GetAwaiter().GetResult()
  $text = $resp.Content.ReadAsStringAsync().GetAwaiter().GetResult()
  if (-not $resp.IsSuccessStatusCode) { Write-Output ('upload FAILED ' + $f + ' HTTP ' + [int]$resp.StatusCode) ; continue }
  $j = $text | ConvertFrom-Json
  Write-Output ('asset OK: ' + $j.name + ' ' + $j.size + ' B state=' + $j.state)
}
Write-Output 'RELEASE DONE'
