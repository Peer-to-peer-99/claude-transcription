$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot

Set-Location $ProjectRoot

Write-Host "======================================"
Write-Host " CLAUDE AUDIÊNCIA - BUILD WINDOWS"
Write-Host "======================================"

$PythonBuild = Join-Path $ProjectRoot "dist\audiencia"

$TauriResources = Join-Path `
    $ProjectRoot `
    "desktop\src-tauri\resources"

$Executable = Join-Path $PythonBuild "audiencia.exe"

if (-not (Test-Path $Executable)) {
    throw "Executável audiencia.exe não encontrado. Gere primeiro o build PyInstaller no Windows."
}

Write-Host "`nPreparando mecanismo de transcrição..."

$Destination = Join-Path $TauriResources "audiencia"

if (Test-Path $Destination) {
    Remove-Item $Destination -Recurse -Force
}

New-Item -ItemType Directory -Path $TauriResources -Force | Out-Null

Copy-Item $PythonBuild $Destination -Recurse -Force

Write-Host "`nGerando instalador Tauri..."

Set-Location (Join-Path $ProjectRoot "desktop")

npm run tauri build -- --bundles nsis

if ($LASTEXITCODE -ne 0) {
    throw "Falha ao gerar instalador."
}

Write-Host "`n======================================"
Write-Host " BUILD WINDOWS CONCLUÍDO"
Write-Host "======================================"

Write-Host "Instalador disponível em:"
Write-Host "desktop\src-tauri\target\release\bundle\nsis\"