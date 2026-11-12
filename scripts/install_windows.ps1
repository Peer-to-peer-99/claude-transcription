$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot

Set-Location $ProjectRoot

Write-Host "======================================"
Write-Host " CLAUDE AUDIÊNCIA - WINDOWS"
Write-Host "======================================"

# Verifica Python
$Python = Get-Command py -ErrorAction SilentlyContinue

if (-not $Python) {

    Write-Host "Python Launcher não encontrado."

    $Winget = Get-Command winget -ErrorAction SilentlyContinue

    if (-not $Winget) {
        throw "Instale o Python 3.12 ou disponibilize o WinGet."
    }

    winget install --id Python.Python.3.12 `
        --exact `
        --scope user `
        --accept-package-agreements `
        --accept-source-agreements

    Write-Host "Python instalado. Abra um novo PowerShell e execute o instalador novamente."

    exit 0
}

# Verifica a versão
py -3.12 --version

if ($LASTEXITCODE -ne 0) {
    throw "Python 3.12 não está disponível."
}

# Executa bootstrap
Write-Host "`nPreparando ambiente Python..."

py -3.12 scripts/bootstrap.py

if ($LASTEXITCODE -ne 0) {
    throw "Falha na instalação das dependências."
}

# Instala Claude Code se necessário
$Claude = Get-Command claude -ErrorAction SilentlyContinue

if (-not $Claude) {

    Write-Host "`nInstalando Claude Code..."

    irm https://claude.ai/install.ps1 | iex
}

Write-Host "`n======================================"
Write-Host " INSTALAÇÃO CONCLUÍDA"
Write-Host "======================================"

Write-Host "Entre na pasta do projeto e execute:"
Write-Host "claude"