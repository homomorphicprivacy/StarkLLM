# StarkLLM Unblock Script
# Safely unblocks extracted files in the current StarkLLM directory only.

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $ScriptDir) {
    $ScriptDir = Get-Location
}

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "         StarkLLM Windows Safety Unblock          " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Unblocking extracted files in local folder:" -ForegroundColor Yellow
Write-Host "  -> $ScriptDir" -ForegroundColor White
Write-Host ""

try {
    Get-ChildItem -Path $ScriptDir -Recurse | Unblock-File -ErrorAction SilentlyContinue
    Write-Host "[SUCCESS] Extracted StarkLLM files in this directory are now unblocked." -ForegroundColor Green
    Write-Host "          You can now run start.exe or start.cmd safely." -ForegroundColor Green
} catch {
    Write-Host "[NOTICE] Files processed. You can now launch start.exe or start.cmd." -ForegroundColor Green
}

Write-Host ""
Write-Host "Press Enter to exit..." -ForegroundColor Gray
[void][System.Console]::ReadLine()
