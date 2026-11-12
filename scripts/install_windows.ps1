$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot

Set-Location $ProjectRoot

Write-Host "======================================"
Write-Host " CLAUDE AUDIÊNCIA - WINDOWS"
Write-Host "======================================"

# ======================================
# CONFIGURAÇÃO DO PATH DO CLAUDE CODE
# ======================================

function Configure-ClaudePath {

    Write-Host "`nConfigurando PATH do Claude Code..."

    $ClaudeDirectory = Join-Path $env:USERPROFILE ".local\bin"
    $ClaudeExecutable = Join-Path $ClaudeDirectory "claude.exe"

    # Verifica se o Claude já está disponível
    $ClaudeCommand = Get-Command claude -ErrorAction SilentlyContinue

    if (-not (Test-Path $ClaudeExecutable)) {

        if ($ClaudeCommand) {
            $ClaudeExecutable = $ClaudeCommand.Source
            $ClaudeDirectory = Split-Path -Parent $ClaudeExecutable
        }
        else {
            throw "Claude Code não encontrado em: $ClaudeExecutable"
        }
    }

    # Recupera o PATH persistente do usuário
    $UserPath = [Environment]::GetEnvironmentVariable(
        "Path",
        "User"
    )

    if ([string]::IsNullOrWhiteSpace($UserPath)) {
        $UserPath = ""
    }

    # Verifica se o diretório já está configurado
    $PathEntries = $UserPath -split ";" |
        ForEach-Object { $_.Trim().TrimEnd("\") }

    $AlreadyConfigured = $PathEntries -contains $ClaudeDirectory.TrimEnd("\")

    # Adiciona ao PATH persistente
    if (-not $AlreadyConfigured) {

        $NewPath = if ([string]::IsNullOrWhiteSpace($UserPath)) {
            $ClaudeDirectory
        }
        else {
            "$UserPath;$ClaudeDirectory"
        }

        [Environment]::SetEnvironmentVariable(
            "Path",
            $NewPath,
            "User"
        )

        Write-Host "Diretório adicionado ao PATH do usuário."
    }
    else {
        Write-Host "Diretório já configurado no PATH."
    }

    # Atualiza o PATH do processo atual
    $CurrentEntries = $env:Path -split ";" |
        ForEach-Object { $_.Trim().TrimEnd("\") }

    if ($CurrentEntries -notcontains $ClaudeDirectory.TrimEnd("\")) {
        $env:Path += ";$ClaudeDirectory"
    }

    # Valida a instalação
    Write-Host "`nValidando Claude Code..."

    & $ClaudeExecutable --version

    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao executar Claude Code."
    }

    Write-Host "Claude Code configurado com sucesso."
}

# ======================================
# PYTHON
# ======================================

Write-Host "`nVerificando Python 3.12..."

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

    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao instalar Python 3.12."
    }

    Write-Host "`nPython instalado."
    Write-Host "Abra um novo PowerShell e execute o instalador novamente."

    exit 0
}

# Verifica a versão
py -3.12 --version

if ($LASTEXITCODE -ne 0) {
    throw "Python 3.12 não está disponível."
}

# ======================================
# DEPENDÊNCIAS PYTHON
# ======================================

Write-Host "`nPreparando ambiente Python..."

py -3.12 scripts/bootstrap.py

if ($LASTEXITCODE -ne 0) {
    throw "Falha na instalação das dependências."
}

# ======================================
# CLAUDE CODE
# ======================================

$Claude = Get-Command claude -ErrorAction SilentlyContinue

if (-not $Claude) {

    Write-Host "`nInstalando Claude Code..."

    irm https://claude.ai/install.ps1 | iex
}

# Configura o PATH e valida
Configure-ClaudePath

# ======================================
# FINALIZAÇÃO
# ======================================

Write-Host "`n======================================"
Write-Host " INSTALAÇÃO CONCLUÍDA"
Write-Host "======================================"

Write-Host "`nFeche este PowerShell e abra outro."

Write-Host "`nEntre na pasta do projeto e execute:"
Write-Host "claude"