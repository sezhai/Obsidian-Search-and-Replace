@echo off
echo ================================
echo Obsidian Search and Replace Tool - Build EXE
echo ================================
echo.

pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing PyInstaller...
    pip install pyinstaller -q
)

echo [INFO] Building EXE file...
echo.

pyinstaller --onefile ^
    --windowed ^
    --name "Obsidian Search and Replace Tool" ^
    --icon=exe.ico ^
    --hidden-import=tkinter ^
    --hidden-import=requests ^
    "Obsidian Search and Replace Tool.py"

if errorlevel 1 (
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

echo.
echo [OK] EXE build completed!
echo Location: dist\Obsidian Search and Replace Tool.exe
echo.
pause