# Build the Windows portable ZIP with Nuitka --standalone.
#
# Nuitka (not PyInstaller, not onefile) is used because the research measured
# a lower VirusTotal false-positive rate for standalone Nuitka builds. Do not
# add UPX or any other packer: packing is what turns heuristic detections into
# reports.
param(
    [Parameter(Mandatory = $true)][string]$Version,
    [string]$Arch = "x64"
)

$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "UTF-8"

# Forward slashes are used throughout: PowerShell and Python accept them on
# Windows, and they survive the YAML/JSON layers that carry this file.
$Root = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
$Build = Join-Path $Root "build"
$NuitkaOutput = Join-Path $Build "nuitka"
$PortableName = "ksnip-pyqt6-$Version-Windows-$Arch-portable"
$Staging = Join-Path $Build $PortableName
$Zip = Join-Path $Build "$PortableName.zip"

$parts = $Version.Split(".")
while ($parts.Count -lt 4) { $parts += "0" }
$WindowsVersion = ($parts[0..3] -join ".")

New-Item -ItemType Directory -Force -Path $NuitkaOutput | Out-Null
Remove-Item (Join-Path $NuitkaOutput "*") -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item $Staging -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item $Zip -Force -ErrorAction SilentlyContinue

Write-Output "Building ksnip-pyqt6 $Version for Windows $Arch"

python -m nuitka `
  --standalone `
  --assume-yes-for-downloads `
  --remove-output `
  --msvc=latest `
  --enable-plugin=pyqt6 `
  --windows-console-mode=disable `
  --windows-icon-from-ico="$Root/packaging/windows/ksnip.ico" `
  --company-name="ksnip" `
  --product-name="ksnip-pyqt6" `
  --file-description="ksnip-pyqt6 screenshot and annotation tool" `
  --file-version="$WindowsVersion" `
  --product-version="$WindowsVersion" `
  --copyright="Copyright (c) 2026 ksnip contributors" `
  --include-package=ksnip_py `
  --include-data-dir="$Root/ksnip_py/icons=ksnip_py/icons" `
  --include-data-dir="$Root/ksnip_py/stickers=ksnip_py/stickers" `
  --include-data-dir="$Root/ksnip_py/translations=ksnip_py/translations" `
  --include-data-dir="$Root/ksnip_py/licenses=ksnip_py/licenses" `
  --nofollow-import-to=PyQt6.QtDBus `
  --nofollow-import-to=paddleocr `
  --nofollow-import-to=paddlepaddle `
  --nofollow-import-to=paddlex `
  --nofollow-import-to=modelscope `
  --nofollow-import-to=markdownify `
  --output-filename="ksnip-pyqt6.exe" `
  --output-dir="$NuitkaOutput" `
  (Join-Path $Root "run_ksnip.py")
if ($LASTEXITCODE -ne 0) { throw "Nuitka failed with exit code $LASTEXITCODE" }

$builtExe = Get-ChildItem -Path $NuitkaOutput -Recurse -Filter "ksnip-pyqt6.exe" |
    Select-Object -First 1
if (-not $builtExe) { throw "Nuitka output executable was not found under $NuitkaOutput" }

# Copy the CONTENTS of the .dist directory. Copying the directory itself
# would nest it inside the staging folder.
New-Item -ItemType Directory -Force -Path $Staging | Out-Null
Copy-Item (Join-Path $builtExe.Directory.FullName "*") $Staging -Recurse -Force
Copy-Item (Join-Path $Root "LICENSE.txt") (Join-Path $Staging "COPYING") -Force
Copy-Item (Join-Path $Root "README.md") (Join-Path $Staging "README.md") -Force

# Build the ZIP with Python: PowerShell 5.1 writes backslash entry names.
python (Join-Path $Root "packaging/scripts/make_portable_zip.py") `
  $Staging $Zip --prefix $PortableName `
  --require "ksnip-pyqt6.exe" --require "COPYING"
if ($LASTEXITCODE -ne 0) { throw "Portable ZIP creation failed with exit code $LASTEXITCODE" }

Write-Output "Created $Zip"
