Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)

function Get-KitSha256 {
    param([string]$Path)
    $algorithm = [Security.Cryptography.SHA256]::Create()
    $stream = [IO.File]::OpenRead($Path)
    try {
        return [BitConverter]::ToString($algorithm.ComputeHash($stream)).Replace('-', '').ToLowerInvariant()
    }
    finally { $stream.Dispose(); $algorithm.Dispose() }
}

function Get-KitManifest {
    param([string]$KitRoot)
    $manifestPath = Join-Path $KitRoot 'bundle-manifest.json'
    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
        throw 'bundle-manifest.json is missing. Extract the complete ZIP first.'
    }
    return Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
}

function Test-KitIntegrity {
    param([string]$KitRoot)
    $rootFull = [IO.Path]::GetFullPath($KitRoot).TrimEnd('\')
    $sumPath = Join-Path $rootFull 'SHA256SUMS'
    if (-not (Test-Path -LiteralPath $sumPath -PathType Leaf)) {
        throw 'SHA256SUMS is missing. Download the complete repository ZIP.'
    }
    $count = 0
    $seen = @{}
    foreach ($line in Get-Content -LiteralPath $sumPath -Encoding UTF8) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        if ($line -notmatch '^([0-9a-f]{64})  (.+)$') {
            throw 'Invalid SHA256SUMS entry.'
        }
        $expected = $Matches[1]
        $relative = $Matches[2]
        if ($seen.ContainsKey($relative)) { throw "Duplicate checksum: $relative" }
        $seen[$relative] = $true
        $fullPath = [IO.Path]::GetFullPath((Join-Path $rootFull $relative))
        if (-not $fullPath.StartsWith($rootFull + '\', [StringComparison]::OrdinalIgnoreCase)) {
            throw "Checksum path leaves the kit: $relative"
        }
        if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) {
            throw "Missing bundle file: $relative"
        }
        $actual = Get-KitSha256 -Path $fullPath
        if ($actual -ne $expected) { throw "SHA256 mismatch: $relative" }
        $count++
    }
    if ($count -lt 5) { throw 'Checksum list is incomplete.' }
    $manifest = Get-KitManifest -KitRoot $rootFull
    foreach ($entry in $manifest.payload) {
        if (-not $seen.ContainsKey([string]$entry.path)) {
            throw "Payload is not covered by SHA256SUMS: $($entry.path)"
        }
        $payloadPath = Join-Path $rootFull ([string]$entry.path)
        $payloadHash = Get-KitSha256 -Path $payloadPath
        if ($payloadHash -ne $entry.sha256) { throw "Manifest mismatch: $($entry.path)" }
    }
    Write-Host "Integrity OK: $count files checked (SHA-256)."
}

function Invoke-KitPython {
    param([string]$PythonPath, [string[]]$Arguments)
    & $PythonPath -X utf8 @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed with exit code $LASTEXITCODE. See logs for details."
    }
}

function Assert-KitPython {
    param([string]$PythonPath, [string]$ExpectedVersion)
    Invoke-KitPython -PythonPath $PythonPath -Arguments @(
        '-I', (Join-Path $PSScriptRoot 'check_python.py'),
        $ExpectedVersion
    )
}

function Expand-KitPython {
    param([string]$Archive, [string]$Destination)
    # Only extract the interpreter's tools/ subtree. Never invoke NuGet or the EXE.
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $destinationFull = [IO.Path]::GetFullPath($Destination).TrimEnd('\')
    $zip = [IO.Compression.ZipFile]::OpenRead($Archive)
    try {
        foreach ($entry in $zip.Entries) {
            if (-not $entry.FullName.StartsWith('tools/', [StringComparison]::Ordinal)) { continue }
            $relative = $entry.FullName.Substring(6)
            if ([string]::IsNullOrEmpty($relative)) { continue }
            $target = [IO.Path]::GetFullPath((Join-Path $destinationFull $relative))
            if (-not $target.StartsWith($destinationFull + '\', [StringComparison]::OrdinalIgnoreCase)) {
                throw "Unsafe archive entry: $($entry.FullName)"
            }
            if ($entry.FullName.EndsWith('/')) {
                [IO.Directory]::CreateDirectory($target) | Out-Null
                continue
            }
            [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($target)) | Out-Null
            [IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $target, $false)
        }
    }
    finally { $zip.Dispose() }
}
