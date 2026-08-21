# ---------------------------------------------------------------------------
# start_dev.ps1 - Servidor de DESENVOLVIMENTO MANUAL do LV Finance
#
# REGRA DE OURO: TESTE AUTOMATIZADO ≠ DESENVOLVIMENTO MANUAL
#
# Este servidor usa SEMPRE o banco persistente dev.sqlite3.
# Nunca aponte este servidor para tmp_validation.sqlite3 ou outro
# banco temporario. A suite de testes nunca usa dev.sqlite3.
#
# Uso:
#   .\start_dev.ps1              # inicia na porta 8010
#   .\start_dev.ps1 -Port 8020   # inicia em outra porta
#   .\start_dev.ps1 -CheckOnly   # apenas mostra a configuracao efetiva
# ---------------------------------------------------------------------------

param(
    [int]$Port = 8010
)

$ErrorActionPreference = "Stop"

$BackendDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $BackendDir "venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    Write-Error "Python do venv nao encontrado em: $Python"
    exit 1
}

# --- Configuracao obrigatoria do ambiente manual ---------------------------
# DATABASE_URL explicita: sobrescreve qualquer coisa (inclusive o .env,
# que aponta para o Neon de producao).
$env:DATABASE_URL = "sqlite:///dev.sqlite3"
$env:DJANGO_DEBUG = "true"
$env:DJANGO_SETTINGS_MODULE = "config.settings"

Push-Location $BackendDir
try {
    # Configuracao efetiva
    $effective = & $Python -c "import os, django; django.setup(); from django.conf import settings; from pathlib import Path; p = Path(str(settings.DATABASES['default']['NAME'])).resolve(); print(p)"
    Write-Host ""
    Write-Host "=== LV Finance - Desenvolvimento Manual ===" -ForegroundColor Cyan
    Write-Host "DATABASE_URL : $env:DATABASE_URL"
    Write-Host "Banco efetivo: $effective"
    Write-Host "DEBUG        : $env:DJANGO_DEBUG"
    Write-Host ""

    if ($effective -notlike "*dev.sqlite3") {
        Write-Host "BLOQUEADO: o banco efetivo nao e dev.sqlite3!" -ForegroundColor Red
        Write-Host "O servidor NAO sera iniciado. Verifique o ambiente." -ForegroundColor Red
        Pop-Location
        exit 1
    }

    if ($MyInvocation.MyCommand.Parameters.Keys -contains "CheckOnly" -and $CheckOnly) {
        Pop-Location
        exit 0
    }

    # Aplica migrations pendentes (idempotente; NUNCA recria o banco)
    & $Python manage.py migrate --noinput
    if ($LASTEXITCODE -ne 0) {
        Pop-Location
        exit 1
    }

    Write-Host ""
    Write-Host "Servidor manual: http://127.0.0.1:$Port" -ForegroundColor Green
    Write-Host "Banco PERSISTENTE: $effective (nao e apagado ao desligar)" -ForegroundColor Green
    Write-Host ""
    & $Python manage.py runserver "127.0.0.1:$Port" --noreload
}
finally {
    Pop-Location
}
