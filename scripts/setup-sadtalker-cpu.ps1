param()
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$env:UV_CACHE_DIR = Join-Path $projectRoot 'work/uv-cache'
$env:UV_PYTHON_INSTALL_DIR = Join-Path $projectRoot 'work/python'
$modelPython = Join-Path $projectRoot 'work/sadtalker/venv/Scripts/python.exe'
$sourceRoot = Join-Path $projectRoot 'work/sadtalker/source'
$sourcePin = 'cd4c0465ae0b54a6f85af57f5c65fec9fe23e7f8'
function Invoke-Checked {
    param([string]$Program, [string[]]$Arguments)
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Program failed with exit code $LASTEXITCODE" }
}
Get-Command uv, git -ErrorAction Stop | Out-Null
Invoke-Checked uv @('python','install','3.10.21','--no-bin','--no-registry')
if (-not (Test-Path -LiteralPath $modelPython)) {
    Invoke-Checked uv @('venv','work/sadtalker/venv','--python','3.10.21')
}
if (-not (Test-Path -LiteralPath (Join-Path $sourceRoot '.git'))) {
    Invoke-Checked git @('-c','http.sslBackend=openssl','clone','--depth','1',
        'https://github.com/OpenTalker/SadTalker.git','work/sadtalker/source')
}
$currentPin = & git -C $sourceRoot rev-parse HEAD
if ($LASTEXITCODE -ne 0) { throw 'Cannot inspect SadTalker checkout' }
if ($currentPin.Trim() -ne $sourcePin) {
    $localChanges = & git -C $sourceRoot status --porcelain
    if ($localChanges) { throw 'Different source version has local changes; preserve it and use a clean checkout.' }
    Invoke-Checked git @('-c','http.sslBackend=openssl','-C',$sourceRoot,'fetch','--depth','1','origin',$sourcePin)
    Invoke-Checked git @('-C',$sourceRoot,'checkout','--detach',$sourcePin)
}
Invoke-Checked uv @('pip','install','--python',$modelPython,'torch==2.6.0','torchvision==0.21.0',
    '--index-url','https://download.pytorch.org/whl/cpu')
Invoke-Checked uv @('pip','install','--python',$modelPython,'-r','requirements-sadtalker-cpu.lock.txt',
    '--index-url','https://pypi.org/simple')
Invoke-Checked $modelPython @('scripts/patch-sadtalker-compat.py')
Invoke-Checked $modelPython @('scripts/download-sadtalker-models.py')
Invoke-Checked uv @('pip','check','--python',$modelPython)
Write-Host 'SadTalker CPU environment and model integrity checks completed. Head quality still needs a local sample review.'
