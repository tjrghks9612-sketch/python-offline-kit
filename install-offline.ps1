#requires -Version 5.1
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'tools\common.ps1')
$kitRoot = [IO.Path]::GetFullPath($PSScriptRoot)
$logRoot = Join-Path $kitRoot 'logs'
[IO.Directory]::CreateDirectory($logRoot) | Out-Null
$transcriptStarted = $false
$exitCode = 1
try {
    Start-Transcript -Path (Join-Path $logRoot ('install-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.log')) | Out-Null
    $transcriptStarted = $true
    if (-not [Environment]::Is64BitOperatingSystem) { throw 'Windows x86-64 is required.' }
    if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64' -or $env:PROCESSOR_ARCHITEW6432 -eq 'ARM64') {
        throw 'This kit is for x86-64 Windows, not ARM64.'
    }
    if ($kitRoot.StartsWith('\\')) { throw 'Extract this kit to a local disk before installing.' }
    if ($kitRoot.Length -gt 100) {
        Write-Warning 'A short path such as C:\AXKit is recommended to avoid Windows path limits.'
    }
    Test-KitIntegrity -KitRoot $kitRoot
    $manifest = Get-KitManifest -KitRoot $kitRoot
    $runtimeRoot = Join-Path $kitRoot ('.runtime\python-' + $manifest.python.version)
    $basePython = Join-Path $runtimeRoot 'python.exe'
    $runtimeMarker = Join-Path $runtimeRoot '.ax-kit-runtime.json'
    if (-not (Test-Path -LiteralPath $basePython -PathType Leaf)) {
        if (Test-Path -LiteralPath $runtimeRoot) {
            throw "Incomplete runtime directory: $runtimeRoot. Keep the log, rename that directory, and retry."
        }
        Write-Host 'Extracting official Python runtime from the local NuGet archive...'
        Expand-KitPython -Archive (Join-Path $kitRoot $manifest.python.runtime_path) -Destination $runtimeRoot
        Assert-KitPython -PythonPath $basePython -ExpectedVersion $manifest.python.version
        @{ archive_sha256 = $manifest.python.runtime_sha256 } |
            ConvertTo-Json | Set-Content -LiteralPath $runtimeMarker -Encoding UTF8
    }
    else {
        if (-not (Test-Path -LiteralPath $runtimeMarker -PathType Leaf)) {
            throw 'Existing runtime is not owned by this kit. Rename .runtime and retry.'
        }
        $marker = Get-Content -LiteralPath $runtimeMarker -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($marker.archive_sha256 -ne $manifest.python.runtime_sha256) {
            throw 'Runtime belongs to a different kit version. Use a fresh extraction folder.'
        }
        Assert-KitPython -PythonPath $basePython -ExpectedVersion $manifest.python.version
    }
    $venvRoot = Join-Path $kitRoot '.venv'
    $venvPython = Join-Path $venvRoot 'Scripts\python.exe'
    $venvMarker = Join-Path $venvRoot '.ax-kit-venv.json'
    if (Test-Path -LiteralPath $venvRoot) {
        if (-not (Test-Path -LiteralPath $venvMarker -PathType Leaf)) {
            throw 'Existing .venv is not owned by this kit. Rename it before retrying.'
        }
        $venvState = Get-Content -LiteralPath $venvMarker -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($venvState.kit_root -ne $kitRoot) {
            throw 'This installed folder has moved. Extract a fresh ZIP in the final location and run setup again.'
        }
    }
    else {
        Write-Host 'Creating the local virtual environment...'
        Invoke-KitPython -PythonPath $basePython -Arguments @('-I', '-m', 'venv', '--without-pip', $venvRoot)
        @{ kit_root = $kitRoot } | ConvertTo-Json | Set-Content -LiteralPath $venvMarker -Encoding UTF8
    }
    Assert-KitPython -PythonPath $venvPython -ExpectedVersion $manifest.python.version
    Invoke-KitPython -PythonPath $venvPython -Arguments @('-I', '-m', 'ensurepip', '--upgrade')
    $pipRunner = Join-Path $kitRoot 'tools\offline_pip.py'
    $wheelRoot = Join-Path $kitRoot 'wheels'
    $pipOptions = @(
        '-I', $pipRunner, '--isolated', '--disable-pip-version-check',
        'install', '--no-index', '--find-links', $wheelRoot,
        '--only-binary=:all:', '--require-hashes', '--no-cache-dir'
    )
    Write-Host 'Installing pinned packaging tools (network is blocked in the pip process)...'
    Invoke-KitPython -PythonPath $venvPython -Arguments ($pipOptions + @('-r', (Join-Path $kitRoot 'bootstrap.lock')))
    Write-Host 'Installing all local wheels and their dependencies...'
    Invoke-KitPython -PythonPath $venvPython -Arguments ($pipOptions + @('-r', (Join-Path $kitRoot 'requirements.lock')))
    Invoke-KitPython -PythonPath $venvPython -Arguments @('-I', $pipRunner, '--isolated', '--disable-pip-version-check', 'check')
    Write-Host 'Running offline functional verification...'
    Invoke-KitPython -PythonPath $venvPython -Arguments @('-I', (Join-Path $kitRoot 'tools\verify_environment.py'), '--root', $kitRoot)
    @{
        status = 'verified'
        python = $venvPython
        base_python = $basePython
        kit_root = $kitRoot
        version = $manifest.python.version
        verified_at = (Get-Date).ToUniversalTime().ToString('o')
    } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $kitRoot '.runtime-info.json') -Encoding UTF8
    Write-Host ''
    Write-Host 'SUCCESS: offline Python is installed and verified.' -ForegroundColor Green
    Write-Host "Python: $venvPython"
    Write-Host "Report: $(Join-Path $kitRoot 'verification-output\verification.json')"
    Write-Host 'For this PowerShell session, run: . .\activate.ps1'
    $exitCode = 0
}
catch {
    @{
        status = 'failed'
        kit_root = $kitRoot
        failed_at = (Get-Date).ToUniversalTime().ToString('o')
        error = $_.Exception.Message
    } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $kitRoot '.runtime-info.json') -Encoding UTF8
    Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Log folder: $logRoot"
}
finally {
    if ($transcriptStarted) { Stop-Transcript | Out-Null }
}
exit $exitCode
