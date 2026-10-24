$ErrorActionPreference = 'Stop'
$round11RenderRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
Push-Location $round11RenderRoot
try {
    $round11WaitStart = Get-Date
    while ($true) {
        $round11HeadState = Get-Content -LiteralPath 'work/round11/head-postprocess-state.json' -Encoding UTF8 -Raw | ConvertFrom-Json
        if ($round11HeadState.status -eq 'head-ready') { break }
        if ($round11HeadState.status -eq 'failed') { throw "Head postprocess failed: $($round11HeadState.error)" }
        if (((Get-Date)-$round11WaitStart).TotalHours -gt 2) { throw 'Head is still processing; preserve and inspect its log.' }
        Start-Sleep -Seconds 5
    }
    & node scripts/build-personal-body-teaching.cjs
    if ($LASTEXITCODE -ne 0) { throw 'Full composition build failed.' }
    $round11Outputs = @('mode1_hands.mp4','mode2_natural.mp4','mode3_lively.mp4')
    foreach ($round11Mode in 1,2,3) {
        & node scripts/hf.cjs history begin --dir "samples/round11/mode$round11Mode" --who codex --label personal-body-teaching
        if ($LASTEXITCODE -ne 0) { throw 'History begin failed.' }
        & node scripts/hf.cjs check "samples/round11/mode$round11Mode" --json 1> "work/round11/mode$round11Mode-check.json" 2> "work/round11/mode$round11Mode-check.stderr.log"
        if ($LASTEXITCODE -ne 0) { throw "Check failed: $round11Mode" }
        $round11Video = 'outputs/round11/' + $round11Outputs[$round11Mode-1]
        if (Test-Path -LiteralPath $round11Video) { throw "Preserve existing output: $round11Video" }
        & node scripts/hf.cjs render "samples/round11/mode$round11Mode" --output $round11Video --fps 24 --quality delivery --workers 1 --no-browser-gpu *> "work/round11/mode$round11Mode-render.log"
        if ($LASTEXITCODE -ne 0) { throw "Render failed: $round11Mode" }
        Write-Output "Round11 mode$round11Mode rendered."
    }
    & node scripts/capture-personal-teaching-alpha.cjs *> work/round11/alpha-capture.log
    if ($LASTEXITCODE -ne 0) { throw 'Transparent-frame capture failed.' }
    & '.\work\sadtalker\venv\Scripts\python.exe' scripts/verify-personal-teaching.py *> work/round11/verification.log
    if ($LASTEXITCODE -ne 0) { throw 'Final video/alpha verification failed.' }
    Write-Output 'All three full13s videos and936 alpha/MP4 frames passed; ready for visual QA and export.'
} finally { Pop-Location }
