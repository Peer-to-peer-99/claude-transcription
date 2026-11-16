$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot

Set-Location $ProjectRoot

Write-Host "======================================"
Write-Host " CLAUDE AUDIÊNCIA - BUILD WINDOWS"
Write-Host "======================================"

# ======================================
# 1. VALIDAR VERSÕES
# ======================================

Write-Host "`nValidando versões do aplicativo..."

$TauriConfig = Get-Content `
    (Join-Path $ProjectRoot "desktop\src-tauri\tauri.conf.json") `
    -Raw | ConvertFrom-Json

$Package = Get-Content `
    (Join-Path $ProjectRoot "desktop\package.json") `
    -Raw | ConvertFrom-Json

$PackageLock = Get-Content `
    (Join-Path $ProjectRoot "desktop\package-lock.json") `
    -Raw | ConvertFrom-Json

$CargoPath = Join-Path $ProjectRoot "desktop\src-tauri\Cargo.toml"
$CargoContent = Get-Content $CargoPath -Raw

if ($CargoContent -notmatch '(?m)^version\s*=\s*"([^"]+)"') {
    throw "Não foi possível identificar a versão do Cargo.toml."
}

$CargoVersion = $Matches[1]

$Versions = [ordered]@{
    Tauri       = $TauriConfig.version
    Cargo       = $CargoVersion
    Package     = $Package.version
    PackageLock = $PackageLock.packages[''].version
}

foreach ($Entry in $Versions.GetEnumerator()) {
    Write-Host "$($Entry.Key): $($Entry.Value)"
}

$UniqueVersions = @($Versions.Values | Select-Object -Unique)

if ($UniqueVersions.Count -ne 1) {
    throw "As versões do aplicativo estão divergentes. Build cancelado."
}

$AppVersion = $TauriConfig.version

Write-Host "`nVersões sincronizadas: $AppVersion"

# ======================================
# 2. VALIDAR EXECUTÁVEL PYTHON
# ======================================

$PythonBuild = Join-Path $ProjectRoot "dist\audiencia"

$TauriResources = Join-Path `
    $ProjectRoot `
    "desktop\src-tauri\resources"

$Executable = Join-Path $PythonBuild "audiencia.exe"

if (-not (Test-Path $Executable)) {
    throw "Executável audiencia.exe não encontrado. Gere primeiro o build PyInstaller no Windows."
}

Write-Host "`nExecutável Python encontrado."

# ======================================
# 3. PREPARAR RECURSOS TAURI
# ======================================

Write-Host "`nPreparando mecanismo de transcrição..."

$Destination = Join-Path $TauriResources "audiencia"

if (Test-Path $Destination) {
    Remove-Item $Destination -Recurse -Force
}

New-Item -ItemType Directory -Path $TauriResources -Force | Out-Null

Copy-Item $PythonBuild $Destination -Recurse -Force

if (-not (Test-Path (Join-Path $Destination "audiencia.exe"))) {
    throw "Falha ao copiar audiencia.exe para os recursos do Tauri."
}

Write-Host "Recursos preparados com sucesso."

# ======================================
# 4. COMPILAR APLICAÇÃO TAURI
# ======================================

Write-Host "`nGerando instalador Tauri..."

Set-Location (Join-Path $ProjectRoot "desktop")

npm run tauri build -- --bundles nsis

if ($LASTEXITCODE -ne 0) {
    throw "Falha ao gerar instalador Tauri."
}

# ======================================
# 5. VALIDAR INSTALADOR
# ======================================

Write-Host "`nValidando instalador gerado..."

$InstallerDirectory = Join-Path `
    $ProjectRoot `
    "desktop\src-tauri\target\release\bundle\nsis"

if (-not (Test-Path $InstallerDirectory)) {
    throw "Diretório do instalador NSIS não encontrado."
}

$Installer = Get-ChildItem `
    -Path $InstallerDirectory `
    -Filter "*-setup.exe" `
    -File |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if (-not $Installer) {
    throw "Instalador NSIS não encontrado."
}

Write-Host "Instalador: $($Installer.Name)"

# ======================================
# 6. RESULTADO
# ======================================

Write-Host "`n======================================"
Write-Host " BUILD WINDOWS CONCLUÍDO"
Write-Host "======================================"

Write-Host "Versão: $AppVersion"
Write-Host "Instalador: $($Installer.FullName)"
Write-Host "Diretório: $InstallerDirectory"