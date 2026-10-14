# Dot-source this file: . .\activate.ps1
$activation = Join-Path $PSScriptRoot '.venv\Scripts\Activate.ps1'
if (-not (Test-Path -LiteralPath $activation)) { throw 'Run setup.cmd first.' }
. $activation
$env:PYTHONUTF8 = '1'
$env:PIP_CONFIG_FILE = 'NUL'
$env:PIP_NO_INDEX = '1'
$env:PIP_FIND_LINKS = Join-Path $PSScriptRoot 'wheels'
$env:PIP_DISABLE_PIP_VERSION_CHECK = '1'
Write-Host "Active Python: $(Join-Path $PSScriptRoot '.venv\Scripts\python.exe')"
