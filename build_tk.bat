@echo off
chcp 65001 >nul
REM PDFmerge Build Script - tkinter version

echo ========================================
echo PDFmerge (tkinter) Build Start
echo ========================================

REM Activate venv if exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Install dependencies
echo.
echo [1/3] Installing dependencies...
pip install pikepdf Pillow tkinterdnd2 pyinstaller

REM Build with PyInstaller
echo.
echo [2/3] Building exe...
pyinstaller build_tk.spec --clean --noconfirm

REM Check result
echo.
echo [3/3] Build completed
if exist dist\PDFmerge_tk.exe (
    echo.
    echo ========================================
    echo SUCCESS: dist\PDFmerge_tk.exe created
    echo ========================================
    dir dist\PDFmerge_tk.exe
) else (
    echo.
    echo ========================================
    echo ERROR: Failed to create exe
    echo ========================================
)

pause
