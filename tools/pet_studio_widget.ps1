$ErrorActionPreference = "Stop"

if ($args.Count -eq 0) {
    Write-Error "Usage: tools\pet_studio_widget.ps1 [pet_studio_widget.py args...]"
    exit 2
}

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$script = Join-Path $root "pet-studio-widget\pet_studio_widget.py"
$logFile = Join-Path $root "pet-studio-widget\project-room-widget.log"
$errFile = Join-Path $root "pet-studio-widget\project-room-widget.err.log"
$candidates = @()

$foreground = $false
$workroom = $args -contains "--workroom"
$windowTitle = if ($workroom) { "Pet Studio Workroom" } else { "Pet Studio Widget" }
foreach ($name in @("--foreground", "--list-projects", "--render-once", "--render-project-once")) {
    if ($args -contains $name) {
        $foreground = $true
        break
    }
}

if ($foreground) {
    if ($env:PET_STUDIO_PYTHON) {
        $candidates += $env:PET_STUDIO_PYTHON
    }
    $candidates += Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    $candidates += "python.exe"
    if ($env:PET_STUDIO_PYTHONW) {
        $candidates += $env:PET_STUDIO_PYTHONW
    }
    $candidates += Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\pythonw.exe"
} else {
    if ($env:PET_STUDIO_PYTHONW) {
        $candidates += $env:PET_STUDIO_PYTHONW
    }
    $candidates += Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\pythonw.exe"
    if ($env:PET_STUDIO_PYTHON) {
        $candidates += $env:PET_STUDIO_PYTHON
    }
    $candidates += Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    $candidates += "pythonw.exe"
}

$python = $null
foreach ($candidate in $candidates) {
    if (-not $candidate) {
        continue
    }
    $command = Get-Command $candidate -ErrorAction SilentlyContinue
    if ($command) {
        $python = $command.Source
        break
    }
    if (Test-Path -LiteralPath $candidate) {
        $python = $candidate
        break
    }
}

if (-not $python) {
    Write-Error "No working Python runtime was found. Set PET_STUDIO_PYTHON or PET_STUDIO_PYTHONW and try again."
    exit 1
}

function Focus-PetStudioWindow {
    param([string]$Title)
    if (-not $IsWindows -and $PSVersionTable.PSEdition -eq "Core") {
        return $false
    }
    $typeName = "PetStudioWidgetWindow"
    if (-not ([System.Management.Automation.PSTypeName]$typeName).Type) {
        Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class PetStudioWidgetWindow {
    [DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);
    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);
}
"@
    }
    $handle = [PetStudioWidgetWindow]::FindWindow($null, $Title)
    if ($handle -eq [IntPtr]::Zero) {
        return $false
    }
    [PetStudioWidgetWindow]::ShowWindow($handle, 9) | Out-Null
    [PetStudioWidgetWindow]::SetForegroundWindow($handle) | Out-Null
    return $true
}

if (-not $foreground) {
    if (Focus-PetStudioWindow $windowTitle) {
        exit 0
    }
}

function Quote-ProcessArgument {
    param([string]$Value)
    if ($Value -match '[\s"]') {
        return '"' + ($Value -replace '"', '\"') + '"'
    }
    return $Value
}

$argumentList = (@($script) + $args | ForEach-Object { Quote-ProcessArgument $_ }) -join " "
if ($foreground) {
    & $python $script @args
    exit $LASTEXITCODE
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $logFile) | Out-Null
Start-Process -FilePath $python -ArgumentList $argumentList -WorkingDirectory $root -WindowStyle Hidden -RedirectStandardOutput $logFile -RedirectStandardError $errFile
