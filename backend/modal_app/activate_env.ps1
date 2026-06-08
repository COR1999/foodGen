# activate_env.ps1 - PowerShell helper that dot-sources the parent .venv Activate.ps1
# Usage from this folder (to affect current session):
#   . .\activate_env.ps1

# Determine project root (parent of this script folder)
$projectRoot = Split-Path -Parent $PSScriptRoot
$activatePath = Join-Path $projectRoot ".venv\Scripts\Activate.ps1"

if (Test-Path $activatePath) {
    # Dot-source so activation affects the current session
    . $activatePath
} else {
    Write-Error "Activate script not found: $activatePath`nRun this from the `modal_app` folder and ensure the .venv is at the project root."
}
