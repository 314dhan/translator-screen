@echo off
echo ============================================================
echo  Translator Screen — Windows Setup
echo ============================================================

echo.
echo [1/3] Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: pip install failed. Make sure Python is in PATH.
    pause
    exit /b 1
)

echo.
echo [2/3] Checking Tesseract OCR...
where tesseract >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  Tesseract NOT found. Please install it manually:
    echo    1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
    echo    2. Run the installer (default path: C:\Program Files\Tesseract-OCR\)
    echo    3. Re-run this script or just run main.py
    echo.
) else (
    echo  Tesseract found: OK
)

echo.
echo [3/3] Done!
echo.
echo  Run the app with:   python main.py
echo.
echo  Controls:
echo    ESC    = quit
echo    F1     = toggle HUD panel
echo    Space  = pause / resume translation
echo.
pause
