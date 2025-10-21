@echo off
REM OralSmart Load Testing Setup Script
REM ==================================

echo.
echo ====================================================
echo  OralSmart Load Testing Setup
echo ====================================================
echo.

REM Check if we're in the right directory
if not exist "src\manage.py" (
    echo ERROR: Django project not found!
    echo Make sure you're running this from the oralsmart root directory.
    echo Expected structure:
    echo   oralsmart/
    echo     src/
    echo       manage.py
    echo       oralsmart/
    echo       patient/
    echo       ...
    echo.
    pause
    exit /b 1
)

echo Step 1: Starting Django Development Server
echo ==========================================
echo.

cd src

REM Check if virtual environment should be activated
if exist "..\venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call ..\venv\Scripts\activate.bat
)

echo Starting Django server on http://localhost:8000...
echo.
echo IMPORTANT: Keep this window open during load testing!
echo To stop the server, press Ctrl+C
echo.
echo Once the server starts, open a new terminal window and run:
echo   python loadtesting/test_server_connectivity.py
echo.

python manage.py runserver

pause