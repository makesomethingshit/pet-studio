$ErrorActionPreference = "Stop"

if ($args.Count -eq 0) {
    Write-Error "Usage: tools\pet_studio_widget.ps1 [pet_studio_widget.py args...]"
    exit 2
}

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$script = Join-Path $root "pet-studio-widget\pet_studio_widget.py"
$candidates = @()

if ($env:PET_STUDIO_PYTHONW) {
    $candidates += $env:PET_STUDIO_PYTHONW
}
$candidates += Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\pythonw.exe"
if ($env:PET_STUDIO_PYTHON) {
    $candidates += $env:PET_STUDIO_PYTHON
}
$candidates += Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$candidates += "pythonw.exe"

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
    Write-Error "No working Python GUI runtime was found. Set PET_STUDIO_PYTHONW to pythonw.exe and try again."
    exit 1
}

function Quote-ProcessArgument {
    param([string]$Value)
    if ($Value -match '[\s"]') {
        return '"' + ($Value -replace '"', '\"') + '"'
    }
    return $Value
}

$argumentList = (@($script) + $args | ForEach-Object { Quote-ProcessArgument $_ }) -join " "
Start-Process -FilePath $python -ArgumentList $argumentList -WorkingDirectory $root -WindowStyle Hidden
