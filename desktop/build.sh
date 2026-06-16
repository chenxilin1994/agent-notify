#!/bin/bash
# Windows Build Script for Agent Notify Desktop App
# Run this on Windows with Git Bash or WSL

cd "$(dirname "$0")"

echo "=== Building Agent Notify Desktop App ==="

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install from https://nodejs.org/"
    exit 1
fi

# Check npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm not found"
    exit 1
fi

echo "✅ Node.js: $(node -v)"
echo "✅ npm: $(npm -v)"

# Install dependencies
echo ""
echo ">>> Installing dependencies..."
npm install

# Check icon
if [ ! -f "icon.ico" ]; then
    echo ""
    echo "⚠️  icon.ico not found"
    echo "   Please create icon.ico (256x256 recommended)"
    echo "   You can use: https://www.icoconverter.com/"
    echo ""
    echo "   For now, creating placeholder..."
    echo "   The app will use default Electron icon"
fi

# Build
echo ""
echo ">>> Building Windows installer..."
npm run build

echo ""
echo "=== Build Complete! ==="
echo ""
echo "Output files in dist/ folder:"
ls -lh dist/ 2>/dev/null || echo "Check dist/ folder manually"
echo ""
echo "You can now:"
echo "  1. Run dist/Agent Notify Setup 1.0.0.exe to install"
echo "  2. Run dist/AgentNotify-Portable.exe directly"