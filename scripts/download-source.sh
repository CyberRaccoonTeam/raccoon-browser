#!/bin/bash
# 🦝 Raccoon Browser - Download Firefox Source
# This script downloads the Firefox source code for building

set -e

FIREFOX_VERSION="148.0.2"
SOURCE_URL="https://archive.mozilla.org/pub/firefox/releases/${FIREFOX_VERSION}/source/firefox-${FIREFOX_VERSION}.source.tar.xz"
OUTPUT_DIR="firefox-source"

echo "🦝 Raccoon Browser - Downloading Firefox Source..."
echo "Version: ${FIREFOX_VERSION}"

if [ -d "$OUTPUT_DIR" ]; then
    echo "✅ Firefox source already exists in $OUTPUT_DIR"
    echo "   To re-download, remove the directory first: rm -rf $OUTPUT_DIR"
    exit 0
fi

echo "📥 Downloading from Mozilla archive..."
mkdir -p "$OUTPUT_DIR"
cd "$OUTPUT_DIR"

# Download and extract
curl -L "$SOURCE_URL" -o firefox-source.tar.xz
tar -xf firefox-source.tar.xz
rm firefox-source.tar.xz

echo "✅ Firefox source downloaded successfully!"
echo "   Location: $(pwd)"
echo ""
echo "Next step: Run ./scripts/apply-branding.sh"
