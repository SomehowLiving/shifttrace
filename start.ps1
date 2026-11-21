# SHIFTTRACE one-command start (Windows PowerShell 5.1+).
#   .\start.ps1            build console if needed, start API + MCP + Cloudflare quick tunnel
#   .\start.ps1 -Rebuild   force a frontend rebuild
#   .\start.ps1 -Reset     reseed the demo database first
param([switch]$Rebuild, [switch]$Reset)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

if ($Rebuild -or -not (Test-Path "$root\frontend\dist\index.html")) {
    Push-Location "$root\frontend"
    if (-not (Test-Path node_modules)) { npm install }
    npx vite build
    Pop-Location
}
Push-Location "$root\backend"
if ($Reset) { uv run python -m app.seed }
Write-Host "Console: http://localhost:8000   Panel simulator: http://localhost:8000/panel"
Write-Host "Preflight (separate terminal): cd backend; uv run python -m app.preflight"
uv run python -m app.main
Pop-Location
