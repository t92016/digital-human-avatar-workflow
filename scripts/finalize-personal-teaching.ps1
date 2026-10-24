$ErrorActionPreference = 'Stop'
$round11Root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$round11Cfg = Get-Content -LiteralPath (Join-Path $round11Root 'config/round11.json') -Encoding UTF8 -Raw | ConvertFrom-Json
$round11Legacy = Get-Content -LiteralPath (Join-Path $round11Root 'work/round11/legacy-source.json') -Encoding UTF8 -Raw | ConvertFrom-Json
$round11Before = [IO.Path]::GetFullPath((Join-Path $round11Root $round11Cfg.legacy_folder))
$round11After = [IO.Path]::GetFullPath((Join-Path $round11Root $round11Cfg.legacy_renamed_folder))
foreach ($round11Target in @($round11Before,$round11After)) {
    if (-not $round11Target.StartsWith($round11Root + '\',[StringComparison]::OrdinalIgnoreCase) -or [IO.Path]::GetDirectoryName($round11Target) -ne $round11Root) { throw 'Rename must stay directly inside the requested workspace.' }
}
if ((Test-Path -LiteralPath $round11Before) -and (Test-Path -LiteralPath $round11After)) { throw 'Both old and renamed folders exist; preserve them and inspect before merging.' }
$round11Source = if (Test-Path -LiteralPath $round11Before) { $round11Before } else { $round11After }
foreach ($round11File in $round11Legacy.files) {
    $round11Actual = (Get-FileHash -LiteralPath (Join-Path $round11Source $round11File.name) -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($round11Actual -ne $round11File.sha256) { throw "Original file changed: $($round11File.name)" }
}
Push-Location $round11Root
try {
    & '.\.venv\Scripts\python.exe' 'scripts/export-personal-teaching.py'
    if ($LASTEXITCODE -ne 0) { throw 'Verified export failed; original folder not renamed.' }
    if (Test-Path -LiteralPath $round11Before) { Rename-Item -LiteralPath $round11Before -NewName $round11Cfg.legacy_renamed_folder }
    foreach ($round11File in $round11Legacy.files) {
        if ((Get-FileHash -LiteralPath (Join-Path $round11After $round11File.name) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $round11File.sha256) { throw 'Original hash changed after rename.' }
    }
    Write-Output 'Verified personal-body delivery exported; original folder renamed without changing its MP4s.'
} finally { Pop-Location }
