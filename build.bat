@echo off
echo ============================================================
echo  Translator Screen — PyInstaller Build
echo ============================================================
echo.
echo This will produce dist\TranslatorScreen\ (~1-2 GB due to EasyOCR/PyTorch).
echo.

pip install pyinstaller --quiet
pyinstaller TranslatorScreen.spec --clean --noconfirm

if %errorlevel% neq 0 (
    echo.
    echo BUILD FAILED. Check the output above for errors.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  Build complete: dist\TranslatorScreen\TranslatorScreen.exe
echo ============================================================
pause
