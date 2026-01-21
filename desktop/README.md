# LingFrame Desktop Application

This directory contains files for building LingFrame as a standalone desktop application.

## Quick Start

### Development Mode (Recommended for Testing)

Run the desktop launcher directly without building:

```bash
# Install dependencies first
pip install pywebview

# Run the desktop app
python desktop/launcher.py
```

### Building Standalone Applications

#### macOS

```bash
# Make the script executable
chmod +x desktop/build_mac.sh

# Build the app
./desktop/build_mac.sh

# Run the app
open dist/LingFrame.app
```

#### Windows

```batch
REM Run the build script
desktop\build_windows.bat

REM Run the executable
dist\LingFrame\LingFrame.exe
```

## Requirements

Before building, ensure you have:

1. **Python 3.9+** with pip
2. **PyInstaller**: `pip install pyinstaller`
3. **PyWebView**: `pip install pywebview`
4. **spaCy model**: `python -m spacy download en_core_web_sm`
5. All project dependencies: `pip install -r requirements.txt`

## App Icons

Place your app icons in this directory:

- `icon.icns` - macOS app icon (required for macOS builds)
- `icon.ico` - Windows app icon (required for Windows builds)

### Creating Icons

**macOS (.icns)**:
1. Create a 1024x1024 PNG image
2. Use the `iconutil` command or apps like "Image2icon"
3. Place the `.icns` file in this directory

**Windows (.ico)**:
1. Create a PNG with multiple sizes (16x16, 32x32, 48x48, 256x256)
2. Use tools like "GIMP" or online converters
3. Place the `.ico` file in this directory

## Architecture

The desktop app works by:

1. Starting a Streamlit server in the background (on localhost)
2. Creating a native OS window using PyWebView
3. Pointing the native window to the Streamlit server
4. Handling graceful shutdown when the window is closed

This approach:
- Reuses all existing Streamlit code
- Provides native window chrome (minimize, maximize, close)
- Works offline without a browser
- Can be distributed as a single app bundle

## Troubleshooting

### "pywebview not found"

```bash
pip install pywebview
```

### "spaCy model not found"

```bash
python -m spacy download en_core_web_sm
```

### Port already in use

The launcher automatically tries alternative ports (8501-8505) if the default is busy.

### Windows WebView2 Runtime

On Windows, PyWebView requires Microsoft Edge WebView2 Runtime. Most Windows 10/11 systems have this pre-installed. If not, download from:
https://developer.microsoft.com/en-us/microsoft-edge/webview2/

### Build fails with missing module

Add the module to the `--hidden-import` flags in the build script.

### App crashes on startup

Check the console output for errors. Common issues:
- Missing spaCy model
- Port conflicts
- Missing dependencies

## Distribution

After building, you can distribute:

- **macOS**: `dist/LingFrame.app` (can be zipped or put in DMG)
- **Windows**: `dist/LingFrame/` folder (contains .exe and dependencies)

For Windows, you may want to create an installer using tools like:
- Inno Setup
- NSIS
- WiX Toolset
