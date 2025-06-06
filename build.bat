@echo off
echo Xbox Controller GUI Build Script
echo ==============================

echo.
echo Checking for pathlib package conflicts...
echo This may take a moment...
python -c "import sys; print('Pathlib conflict detected!' if any('pathlib' in str(p) for p in sys.path if 'site-packages' in str(p)) else 'No pathlib conflicts found')"

echo.
echo If you see a pathlib conflict above, please run:
echo conda remove pathlib
echo Then run this script again.
echo.

echo Installing requirements...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error installing requirements!
    pause
    exit /b 1
)

echo.
echo Installing PyInstaller...
pip install pyinstaller
if %errorlevel% neq 0 (
    echo Error installing PyInstaller!
    pause
    exit /b 1
)

echo.
echo Running setup to create spec file...
python setup.py
if %errorlevel% neq 0 (
    echo Error running setup!
    pause
    exit /b 1
)

echo.
echo Building executable...
pyinstaller joystick_gui.spec
if %errorlevel% neq 0 (
    echo Error building executable!
    pause
    exit /b 1
)

echo.
echo Build complete!
echo The executable is located in: dist\Xbox_Controller_GUI.exe
echo.
pause
