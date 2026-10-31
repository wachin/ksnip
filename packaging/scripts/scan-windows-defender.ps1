# Scan one or more Windows artifacts with Microsoft Defender.
#
# VirusTotal scanning an installer or a ZIP does not scan the executable inside
# it.  A clean installer can therefore still deliver an executable that Windows
# Defender removes as Trojan:Win32/Wacatac.C!ml.  This script scans the file it
# is given, with remediation disabled, so the artifact survives the scan and the
# build can report the detection instead of silently losing its payload.
#
# Exit codes: 0 clean or Defender unavailable; 2 at least one threat detected
# (the build step turns that into a failure).
param(
    [Parameter(Mandatory = $true)][string[]]$Path,
    [switch]$AllowMissing
)

$ErrorActionPreference = "Stop"

function Find-MpCmdRun {
    $platformRoot = Join-Path $env:ProgramData "Microsoft\Windows Defender\Platform"
    if (Test-Path $platformRoot) {
        $candidate = Get-ChildItem $platformRoot -Filter "MpCmdRun.exe" -Recurse -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1
        if ($candidate) { return $candidate }
    }

    $fallback = Join-Path $env:ProgramFiles "Windows Defender\MpCmdRun.exe"
    if (Test-Path $fallback) { return Get-Item $fallback }

    return $null
}

$mp = Find-MpCmdRun
if (-not $mp) {
    if ($AllowMissing) {
        Write-Warning "MpCmdRun.exe was not found; skipping the Microsoft Defender scan."
        exit 0
    }
    throw "MpCmdRun.exe was not found. Run this on Windows with Microsoft Defender installed."
}

$detected = @()
foreach ($item in $Path) {
    if (-not (Test-Path $item)) {
        throw "The file to scan does not exist: $item"
    }
    $resolved = (Resolve-Path $item).Path
    Write-Output "Scanning $resolved with $($mp.FullName)"
    & $mp.FullName -Scan -ScanType 3 -File $resolved -DisableRemediation
    $code = $LASTEXITCODE
    if ($code -eq 2) {
        $detected += $resolved
    } elseif ($code -ne 0) {
        Write-Warning "MpCmdRun.exe exited with code $code for $resolved; the result is not conclusive."
    }
}

if ($detected.Count -gt 0) {
    throw "Microsoft Defender detected a threat in: $($detected -join ', '). Do not publish this artifact."
}

Write-Output "Microsoft Defender reported no threat."
exit 0
