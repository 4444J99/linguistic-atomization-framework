@echo off
REM Build LingFrame desktop application for Windows
REM
REM Prerequisites:
REM   pip install pyinstaller pywebview
REM   python -m spacy download en_core_web_sm
REM
REM Usage:
REM   desktop\build_windows.bat
REM
REM Output:
REM   dist\LingFrame\LingFrame.exe

setlocal enabledelayedexpansion

echo.
echo ====================================
echo   Building LingFrame for Windows
echo ====================================
echo.

REM Get script directory and project root
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

cd /d "%PROJECT_ROOT%"
echo    Project root: %PROJECT_ROOT%

REM Ensure build dependencies are installed
echo.
echo [1/4] Checking dependencies...
pip install pyinstaller pywebview --quiet

REM Clean previous builds
echo.
echo [2/4] Cleaning previous builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.spec" del /f /q "*.spec"

REM Build with PyInstaller
echo.
echo [3/4] Building with PyInstaller...

pyinstaller ^
    --name "LingFrame" ^
    --windowed ^
    --onedir ^
    --noconfirm ^
    --clean ^
    --add-data "app;app" ^
    --add-data "framework;framework" ^
    --add-data "templates;templates" ^
    --collect-data spacy ^
    --collect-data en_core_web_sm ^
    --collect-data streamlit ^
    --collect-data altair ^
    --collect-data vaderSentiment ^
    --hidden-import webview ^
    --hidden-import webview.platforms.edgechromium ^
    --hidden-import webview.platforms.mshtml ^
    --hidden-import streamlit ^
    --hidden-import spacy ^
    --hidden-import sklearn ^
    --hidden-import sklearn.feature_extraction.text ^
    --hidden-import pdfplumber ^
    --hidden-import fitz ^
    --hidden-import PIL ^
    --hidden-import textblob ^
    --hidden-import vaderSentiment ^
    --hidden-import plotly ^
    --hidden-import numpy ^
    --hidden-import pandas ^
    --icon "desktop\icon.ico" ^
    desktop\launcher.py

REM Check if build succeeded
echo.
echo [4/4] Verifying build...

if exist "dist\LingFrame\LingFrame.exe" (
    echo.
    echo ====================================
    echo   Build successful!
    echo ====================================
    echo.
    echo    Executable: %PROJECT_ROOT%\dist\LingFrame\LingFrame.exe
    echo.
    echo    To run: dist\LingFrame\LingFrame.exe
    echo.
) else (
    echo.
    echo ====================================
    echo   Build FAILED!
    echo ====================================
    exit /b 1
)

echo Done!
endlocal
