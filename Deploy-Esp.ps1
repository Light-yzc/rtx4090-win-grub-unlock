<#
.SYNOPSIS
    Deploy staged RTX 4090 Windows UEFI Unlock files to the Windows EFI System Partition (ESP).
.DESCRIPTION
    Mounts the Windows EFI System Partition temporarily (or uses an existing drive letter),
    verifies the presence of \EFI\Microsoft\Boot\bootmgfw.efi, and copies:
      - \EFI\RTX4090-UNLOCK\BOOTX64.EFI
      - \RTX4090-UNLOCK\ASSETS\* (5 pinned firmware assets)
    Run this script from an Administrator PowerShell prompt.
#>
param(
    [string]$MountLetter = "S:",
    [switch]$KeepMounted
)

$ErrorActionPreference = "Stop"
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$DistEsp = Join-Path $Here "dist\esp"

if (-not (Test-Path (Join-Path $DistEsp "EFI\RTX4090-UNLOCK\BOOTX64.EFI"))) {
    throw "Staged files not found in $DistEsp. Run 'python stage-esp.py' first."
}

$MountedByScript = $false
if (-not (Test-Path "$MountLetter\")) {
    Write-Host "[*] Mounting EFI System Partition to $MountLetter ..."
    mountvol $MountLetter /S
    if ($LASTEXITCODE -ne 0) {
        throw "mountvol $MountLetter /S failed (exit code $LASTEXITCODE). Run PowerShell as Administrator."
    }
    $MountedByScript = $true
}

try {
    $Bootmgfw = Join-Path "$MountLetter\" "EFI\Microsoft\Boot\bootmgfw.efi"
    if (-not (Test-Path $Bootmgfw)) {
        throw "Could not find $Bootmgfw on $MountLetter. Refusing to deploy to an unexpected volume."
    }

    $TargetEfiDir = Join-Path "$MountLetter\" "EFI\RTX4090-UNLOCK"
    $TargetAssetsDir = Join-Path "$MountLetter\" "RTX4090-UNLOCK\ASSETS"

    New-Item -ItemType Directory -Force -Path $TargetEfiDir | Out-Null
    New-Item -ItemType Directory -Force -Path $TargetAssetsDir | Out-Null

    Copy-Item -Force (Join-Path $DistEsp "EFI\RTX4090-UNLOCK\BOOTX64.EFI") (Join-Path $TargetEfiDir "BOOTX64.EFI")
    Copy-Item -Force (Join-Path $DistEsp "RTX4090-UNLOCK\ASSETS\*") $TargetAssetsDir

    $EfiHash = (Get-FileHash -Algorithm SHA256 (Join-Path $TargetEfiDir "BOOTX64.EFI")).Hash.ToLower()
    Write-Host "[+] Deployed \EFI\RTX4090-UNLOCK\BOOTX64.EFI (SHA-256: $EfiHash)"
    Get-ChildItem $TargetAssetsDir | ForEach-Object {
        $h = (Get-FileHash -Algorithm SHA256 $_.FullName).Hash.ToLower()
        Write-Host "[+] Deployed \RTX4090-UNLOCK\ASSETS\$($_.Name) ($($_.Length) bytes, SHA-256: $h)"
    }
    Write-Host "[+] ESP deployment complete. Logs will be written to \RTX4090-UNLOCK\RUN00..RUN99\REPORT.TXT on boot."
}
finally {
    if ($MountedByScript -and -not $KeepMounted) {
        Write-Host "[*] Unmounting $MountLetter ..."
        mountvol $MountLetter /D
    }
}

