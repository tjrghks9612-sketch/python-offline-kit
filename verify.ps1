#requires -Version 5.1
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'tools\common.ps1')
try {
    Test-KitIntegrity -KitRoot $PSScriptRoot
    $manifest = Get-KitManifest -KitRoot $PSScriptRoot
    $pythonPath = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
    Assert-KitPython -PythonPath $pythonPath -ExpectedVersion $manifest.python.version
    Invoke-KitPython -PythonPath $pythonPath -Arguments @('-I', (Join-Path $PSScriptRoot 'tools\offline_pip.py'), '--isolated', '--disable-pip-version-check', 'check')
    Invoke-KitPython -PythonPath $pythonPath -Arguments @('-I', (Join-Path $PSScriptRoot 'tools\verify_environment.py'), '--root', $PSScriptRoot)
}
catch {
    Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
exit 0
