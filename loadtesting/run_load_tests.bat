@echo off
REM OralSmart Load Testing Launcher (Windows Batch)
REM ===============================================
REM Simple wrapper to run enhanced load tests on Windows

setlocal enabledelayedexpansion

echo 🚀 OralSmart Load Testing Launcher (Windows)
echo ==========================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "loadtesting\enhanced_load_test.py" (
    echo ❌ Please run this script from the oralsmart project root directory
    pause
    exit /b 1
)

REM Install dependencies if needed
if not exist "venv\" (
    echo 📦 Installing virtual environment...
    python -m venv venv
)

echo 📦 Activating virtual environment...
call venv\Scripts\activate.bat

echo 📦 Installing/updating dependencies...
pip install -r requirements-loadtest.txt

REM Show menu if no arguments provided
if "%1"=="" (
    echo.
    echo Choose a testing preset:
    echo 1. Super Quick Test ^(30 seconds per test, 1 iteration^)
    echo 2. Quick Test ^(2 iterations, light + moderate load^)
    echo 3. Full Test ^(3 iterations, all scenarios^)
    echo 4. Stress Test ^(3 iterations, heavy load only^)
    echo 5. Development Test ^(1 iteration, light load only^)
    echo 6. Exit
    echo.
    set /p choice="Enter your choice (1-6): "
) else (
    set choice=%1
)

REM Map choices to commands
if "%choice%"=="1" set cmd=python loadtesting\enhanced_load_test.py --iterations=1 --scenarios quick_test --check-server
if "%choice%"=="2" set cmd=python loadtesting\enhanced_load_test.py --iterations=2 --scenarios light_load moderate_load --check-server
if "%choice%"=="3" set cmd=python loadtesting\enhanced_load_test.py --iterations=3 --check-server
if "%choice%"=="4" set cmd=python loadtesting\enhanced_load_test.py --iterations=3 --scenarios heavy_load --check-server
if "%choice%"=="5" set cmd=python loadtesting\enhanced_load_test.py --iterations=1 --scenarios light_load --check-server
if "%choice%"=="6" exit /b 0

if "!cmd!"=="" (
    echo ❌ Invalid choice!
    pause
    exit /b 1
)

echo.
echo 🔧 Running load test...
echo Command: !cmd!
echo.
echo ⏳ This may take several minutes. Please wait...

REM Run the command
!cmd!

if errorlevel 1 (
    echo.
    echo ❌ Load testing failed. Check the error messages above.
    pause
    exit /b 1
) else (
    echo.
    echo ✅ Load testing completed successfully!
    echo 📊 Check the loadtesting\reports\ directory for graphs and results.
    echo.
    
    REM Open the reports directory in Explorer
    if exist "loadtesting\reports\" (
        echo 📁 Opening reports directory...
        start explorer "loadtesting\reports\"
    )
)

echo.
echo Press any key to exit...
pause >nul