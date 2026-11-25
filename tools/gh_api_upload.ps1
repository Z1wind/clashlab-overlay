param(
  [Parameter(Mandatory=$true)][string]$Token,
  [string]$Owner = 'Z1wind',
  [string]$Repo = 'clashlab-overlay',
  [string]$Branch = 'main',
  [int]$Batch = 24
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$git = Join-Path $env:TEMP 'gitportable\mingit\cmd\git.exe'

Add-Type -AssemblyName System.Net.Http
$client = New-Object System.Net.Http.HttpClient
$client.Timeout = [TimeSpan]::FromMinutes(10)
$client.DefaultRequestHeaders.Add('User-Agent', 'clashlab-uploader')
$client.DefaultRequestHeaders.Add('Authorization', ('token ' + $Token))
$api = 'https://api.github.com'
$repoApi = $api + '/repos/' + $Owner + '/' + $Repo

function JsonReq([string]$method, [string]$url, $obj) {
  $req = New-Object System.Net.Http.HttpRequestMessage([System.Net.Http.HttpMethod]::new($method), $url)
  if ($null -ne $obj) {
    $json = $obj | ConvertTo-Json -Depth 20 -Compress
    $req.Content = New-Object System.Net.Http.StringContent($json, [Text.Encoding]::UTF8, 'application/json')
  }
  return $req
}

function SendAll($reqs) {
  $tasks = @()
  foreach ($r in $reqs) { $tasks += $client.SendAsync($r) }
  [System.Threading.Tasks.Task]::WaitAll($tasks)
  $out = @()
  foreach ($t in $tasks) {
    $resp = $t.Result
    $text = $resp.Content.ReadAsStringAsync().GetAwaiter().GetResult()
    if (-not $resp.IsSuccessStatusCode) { throw ('HTTP ' + [int]$resp.StatusCode + ' :: ' + $text.Substring(0, [Math]::Min(260, $text.Length))) }
    $out += ($text | ConvertFrom-Json)
  }
  return $out
}

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$files = & $git -c core.quotepath=false ls-files
$files = @($files | Where-Object { $_ -and (Test-Path (Join-Path $root $_)) })
Write-Output ('files: ' + $files.Count)
$entries = New-Object System.Collections.ArrayList
$batchReqs = @(); $batchRel = @()
foreach ($rel in $files) {
  $bytes = [IO.File]::ReadAllBytes((Join-Path $root $rel))
  $b64 = [Convert]::ToBase64String($bytes)
  $batchReqs += (JsonReq 'POST' ($repoApi + '/git/blobs') @{ content = $b64; encoding = 'base64' })
  $batchRel += $rel
  if ($batchReqs.Count -ge $Batch) {
    $res = SendAll $batchReqs
    for ($k = 0; $k -lt $batchRel.Count; $k++) { [void]$entries.Add(@{ path = $batchRel[$k]; mode = '100644'; type = 'blob'; sha = $res[$k].sha }) }
    Write-Output ('  blobs: ' + $entries.Count + ' / ' + $files.Count)
    $batchReqs = @(); $batchRel = @()
  }
}
if ($batchReqs.Count -gt 0) {
  $res = SendAll $batchReqs
  for ($k = 0; $k -lt $batchRel.Count; $k++) { [void]$entries.Add(@{ path = $batchRel[$k]; mode = '100644'; type = 'blob'; sha = $res[$k].sha }) }
  Write-Output ('  blobs: ' + $entries.Count + ' / ' + $files.Count)
}
Write-Output ('blobs done: ' + $entries.Count)
$parent = SendAll @(JsonReq 'GET' ($repoApi + '/git/ref/heads/' + $Branch) $null)
$parentSha = $parent[0].object.sha
Write-Output ('parent: ' + $parentSha)
$tree = SendAll @(JsonReq 'POST' ($repoApi + '/git/trees') @{ tree = $entries })
Write-Output ('tree: ' + $tree[0].sha)
$commit = SendAll @(JsonReq 'POST' ($repoApi + '/git/commits') @{ message = 'chore: initial open-source release v0.1.0 (imported via API)'; tree = $tree[0].sha; parents = @($parentSha) })
Write-Output ('commit: ' + $commit[0].sha)
$ref = SendAll @(JsonReq 'PATCH' ($repoApi + '/git/refs/heads/' + $Branch) @{ sha = $commit[0].sha; force = $true })
Write-Output ('ref: ' + $ref[0].ref + ' -> ' + $ref[0].object.sha)
$v = SendAll @(JsonReq 'GET' ($repoApi + '/git/trees/' + $Branch + '?recursive=1') $null)
Write-Output ('remote entries: ' + $v[0].tree.Count)
Write-Output 'DONE'
