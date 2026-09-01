@echo off
echo ============================================
echo   NebulaForge X300 - Windows Setup
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

echo [1/3] Python found. Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo [2/3] Dependencies installed successfully.
echo.
echo [3/3] Starting NebulaForge...
echo.

python main.pyw

if errorlevel 1 (
    echo.
    echo ERROR: Application failed to start.
    echo Check the error message above for details.
    pause
)
