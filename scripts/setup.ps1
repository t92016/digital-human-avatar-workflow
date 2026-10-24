param([string]$PythonCommand = 'python', [switch]$RenderTools)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $projectRoot
try {
    New-Item -ItemType Directory -Path 'work' -Force | Out-Null
    $pythonExe = Join-Path $projectRoot '.venv\Scripts\python.exe'
    if (!(Test-Path -LiteralPath $pythonExe)) {
        if (Get-Command uv -ErrorAction SilentlyContinue) {
            & uv venv .venv --python $PythonCommand --cache-dir work/uv-cache
        } else {
            & $PythonCommand -m venv .venv
        }
        if ($LASTEXITCODE -ne 0) { throw '建立 Python 虛擬環境失敗' }
    }
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        & uv pip install --python $pythonExe --only-binary :all: --cache-dir work/uv-cache -r requirements-prototype.lock.txt
    } else {
        & $pythonExe -m pip install --only-binary :all: -r requirements-prototype.lock.txt
    }
    if ($LASTEXITCODE -ne 0) { throw '安裝 Python 套件失敗' }
    & npm.cmd --cache work/npm-cache ci --ignore-scripts --no-fund
    if ($LASTEXITCODE -ne 0) { throw '安裝 Node 套件失敗' }
    & $pythonExe -m avatar_workflow doctor
    if ($RenderTools) {
        & $pythonExe -m avatar_workflow tools --ffmpeg
        if ($LASTEXITCODE -ne 0) { throw '安裝影音工具失敗' }
        & node scripts/install-browser.mjs
        if ($LASTEXITCODE -ne 0) { throw '安裝獨立渲染瀏覽器失敗' }
    }
} finally { Pop-Location }
