@echo off
chcp 65001 >nul
REM PDFmerge Build Script (Windows)

echo ========================================
echo PDFmerge Build Start
echo ========================================

REM Activate venv if exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Install dependencies
echo.
echo [1/3] Installing dependencies...
pip install -r requirements.txt

REM Build with PyInstaller
echo.
echo [2/3] Building exe...
pyinstaller build.spec --clean --noconfirm

REM Check result
echo.
echo [3/3] Build completed
if exist dist\PDFmerge.exe (
    echo.
    echo ========================================
    echo SUCCESS: dist\PDFmerge.exe created
    echo ========================================
    dir dist\PDFmerge.exe
) else (
    echo.
    echo ========================================
    echo ERROR: Failed to create exe
    echo ========================================
)

pause
