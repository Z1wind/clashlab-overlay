$files = @()
foreach ($n in @('b10','b11','b12','b14','b15','b16','b17','b18','b19','b20')) {
  $p = Join-Path $env:USERPROFILE ('Downloads\annot_' + $n + '.json')
  if (Test-Path $p) { $files += $p } else { Write-Output ('MISSING ' + $p) }
}
Write-Output ('count=' + $files.Count)
& 'D:/Python313/python.exe' -u 'tools/label_qa.py' --labels @files