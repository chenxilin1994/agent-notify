# Windows Build Script for Agent Notify Desktop App
# Run this in PowerShell

Write-Host "=== Building Agent Notify Desktop App ===" -ForegroundColor Green

# Check Node.js
try {
    $nodeVersion = node -v
    Write-Host "✅ Node.js: $nodeVersion" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Node.js not found. Please install from https://nodejs.org/" -ForegroundColor Red
    exit 1
}

# Check npm
try {
    $npmVersion = npm -v
    Write-Host "✅ npm: $npmVersion" -ForegroundColor Cyan
} catch {
    Write-Host "❌ npm not found" -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host ""
Write-Host ">>> Installing dependencies..." -ForegroundColor Yellow
npm install

# Check icon
if (-Not (Test-Path "icon.ico")) {
    Write-Host ""
    Write-Host "⚠️  icon.ico not found" -ForegroundColor Yellow
    Write-Host "   Please create icon.ico (256x256 recommended)"
    Write-Host "   You can use: https://www.icoconverter.com/"
    Write-Host ""
    Write-Host "   For now, the app will use default Electron icon"
    Write-Host ""
}

# Build
Write-Host ""
Write-Host ">>> Building Windows installer..." -ForegroundColor Yellow
npm run build

Write-Host ""
Write-Host "=== Build Complete! ===" -ForegroundColor Green
Write-Host ""
Write-Host "Output files in dist folder:"
Get-ChildItem dist | Format-Table Name, Length -AutoSize

Write-Host ""
Write-Host "You can now:" -ForegroundColor Cyan
Write-Host "  1. Run dist\Agent Notify Setup 1.0.0.exe to install"
Write-Host "  2. Run dist\AgentNotify-Portable.exe directly"