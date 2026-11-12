$ErrorActionPreference = "Stop"

$Script = Join-Path $PSScriptRoot "scripts/install_windows.ps1"

& $Script

if ($LASTEXITCODE -ne 0) {
    throw "A instalação falhou."
}