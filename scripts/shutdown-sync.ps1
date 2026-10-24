param([switch]$Commit,[switch]$Push,[string]$Message='chore: sync project progress')
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $projectRoot
try {
 $python=Join-Path $projectRoot '.venv/Scripts/python.exe'
 if (!(Test-Path -LiteralPath $python)) { $python='python' }
 $env:PYTHONIOENCODING='utf-8'
 & $python scripts/secret-scan.py
 if ($LASTEXITCODE -ne 0) { throw 'Public-file or secret scan failed; nothing committed or pushed.' }
 $progress=Join-Path $projectRoot '專案進度.md'
 $zone=[TimeZoneInfo]::FindSystemTimeZoneById('Taipei Standard Time')
 $stamp=[TimeZoneInfo]::ConvertTimeFromUtc([DateTime]::UtcNow,$zone).ToString('yyyy-MM-dd HH:mm:ss')
 $text=[IO.File]::ReadAllText($progress)
 if ($text -match '(?m)^最後收工時間：.*$') { $text=[regex]::Replace($text,'(?m)^最後收工時間：.*$',"最後收工時間：$stamp（Asia/Taipei）") }
 else { $text=$text.Replace('# 專案進度',"# 專案進度`n`n最後收工時間：$stamp（Asia/Taipei）") }
 [IO.File]::WriteAllText($progress,$text,[Text.UTF8Encoding]::new($false))
 if (Get-Command chezmoi -ErrorAction SilentlyContinue) {
  try {
   $chezmoiStatus=& chezmoi status 2>&1
   $chezmoiStatus | Set-Content -LiteralPath 'work/publication/chezmoi-status.txt' -Encoding UTF8
   if ($LASTEXITCODE -ne 0) { Write-Warning 'chezmoi status unavailable; no home settings were changed.' }
   else { Write-Host 'chezmoi status recorded privately; no settings applied.' }
  }
  catch { Write-Warning 'chezmoi status could not run; no home settings were changed.' }
 }
 if ($Commit) {
  & $python scripts/secret-scan.py
  if ($LASTEXITCODE -ne 0) { throw 'Scan failed after progress update' }
  $report=Get-Content -LiteralPath 'work/publication/secret-scan.json' -Raw -Encoding UTF8 | ConvertFrom-Json
  foreach ($entry in $report.entries) { & git add -- $entry.path; if ($LASTEXITCODE -ne 0) { throw 'git add failed' } }
  & git add --renormalize -- .
  if ($LASTEXITCODE -ne 0) { throw 'Apply repository byte-preservation attributes failed' }
  & $python scripts/secret-scan.py --staged --report work/publication/staged-scan.json
  if ($LASTEXITCODE -ne 0) { throw 'Staged-index scan failed' }
  & git diff --cached --quiet
  if ($LASTEXITCODE -eq 1) { & git commit -m $Message; if ($LASTEXITCODE -ne 0) { throw 'git commit failed' } }
 }
 if ($Push) {
  & $python scripts/secret-scan.py --staged --report work/publication/staged-scan.json
  if ($LASTEXITCODE -ne 0) { throw 'Staged scan failed' }
  $branch=(& git branch --show-current).Trim()
  if (!$branch) { throw 'No branch; select the intended branch before pushing' }
  & git push -u origin $branch
  if ($LASTEXITCODE -ne 0) { throw 'Push did not complete; retain local files and report the actual failure.' }
 }
 Write-Host "Shutdown scan completed: $stamp Asia/Taipei. Commit=$Commit Push=$Push"
} finally { Pop-Location }
