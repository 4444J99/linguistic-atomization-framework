#!/bin/bash
# Build LingFrame desktop application for macOS
#
# Prerequisites:
#   pip install pyinstaller pywebview
#   python -m spacy download en_core_web_sm
#
# Usage:
#   ./desktop/build_mac.sh
#
# Output:
#   dist/LingFrame.app

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🏗️  Building LingFrame for macOS..."
echo "   Project root: $PROJECT_ROOT"

cd "$PROJECT_ROOT"

# Ensure build dependencies are installed
echo "📦 Checking dependencies..."
pip install pyinstaller pywebview --quiet

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build dist *.spec

# Determine spaCy model path
SPACY_MODEL_PATH=$(python -c "import spacy; import os; print(os.path.dirname(spacy.load('en_core_web_sm').__path__))" 2>/dev/null || echo "")

if [ -z "$SPACY_MODEL_PATH" ]; then
    echo "⚠️  Warning: spaCy model not found. Run: python -m spacy download en_core_web_sm"
fi

# Build with PyInstaller
echo "🔨 Building with PyInstaller..."

pyinstaller \
    --name "LingFrame" \
    --windowed \
    --onedir \
    --noconfirm \
    --clean \
    --add-data "app:app" \
    --add-data "framework:framework" \
    --add-data "templates:templates" \
    --collect-data spacy \
    --collect-data en_core_web_sm \
    --collect-data streamlit \
    --collect-data altair \
    --collect-data vaderSentiment \
    --hidden-import webview \
    --hidden-import webview.platforms.cocoa \
    --hidden-import streamlit \
    --hidden-import spacy \
    --hidden-import sklearn \
    --hidden-import sklearn.feature_extraction.text \
    --hidden-import pdfplumber \
    --hidden-import fitz \
    --hidden-import PIL \
    --hidden-import textblob \
    --hidden-import vaderSentiment \
    --hidden-import plotly \
    --hidden-import numpy \
    --hidden-import pandas \
    --icon "desktop/icon.icns" \
    --osx-bundle-identifier "com.lingframe.app" \
    desktop/launcher.py

# Check if build succeeded
if [ -d "dist/LingFrame.app" ]; then
    echo ""
    echo "✅ Build successful!"
    echo "   App location: $PROJECT_ROOT/dist/LingFrame.app"
    echo ""
    echo "   To run: open dist/LingFrame.app"
    echo "   To install: drag LingFrame.app to /Applications"
else
    echo "❌ Build failed!"
    exit 1
fi

# Optional: Create DMG installer
if command -v create-dmg &> /dev/null; then
    echo "📀 Creating DMG installer..."
    create-dmg \
        --volname "LingFrame Installer" \
        --window-size 600 400 \
        --icon "LingFrame.app" 150 150 \
        --app-drop-link 450 150 \
        "dist/LingFrame-Installer.dmg" \
        "dist/LingFrame.app"
    echo "   DMG location: $PROJECT_ROOT/dist/LingFrame-Installer.dmg"
fi

echo ""
echo "🎉 Done!"
