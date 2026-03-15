#!/bin/bash
# 🦝 Raccoon Browser - Apply Raccoon Branding
# This script applies Raccoon branding to Firefox source

set -e

BRANDING_SOURCE="../raccoon-browser-fork/librewolf-source"
BRANDING_DEST="firefox-source/browser/branding/raccoon"

echo "🦝 Raccoon Browser - Applying Branding..."

if [ ! -d "firefox-source" ]; then
    echo "❌ Firefox source not found!"
    echo "   Run ./scripts/download-source.sh first"
    exit 1
fi

# Create branding directory
mkdir -p "$BRANDING_DEST"

# Copy branding files from LibreWolf fork
if [ -d "$BRANDING_SOURCE" ]; then
    echo "📋 Copying branding files from LibreWolf fork..."
    cp -r "$BRANDING_SOURCE/browser/branding/"* "$BRANDING_DEST/" 2>/dev/null || true
    echo "✅ Branding files copied"
else
    echo "⚠️  LibreWolf source not found at $BRANDING_SOURCE"
    echo "   Manual branding setup required"
fi

# Apply mozconfig
if [ -f "../mozconfig.raccoon" ]; then
    echo "📋 Applying mozconfig..."
    cp ../mozconfig.raccoon firefox-source/mozconfig
    echo "✅ mozconfig applied"
fi

echo ""
echo "✅ Branding applied successfully!"
echo ""
echo "Next step: Build the browser"
echo "   cd firefox-source"
echo "   ./mach build"
