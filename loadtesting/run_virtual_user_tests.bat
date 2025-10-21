@echo off
REM Virtual User Load Testing Launcher for OralSmart
REM Quick access to common test scenarios

echo.
echo ====================================================
echo  OralSmart Virtual User Load Testing
echo ====================================================
echo.
echo Available Test Scenarios:
echo.
echo 1. Patient management workflow - 500 virtual users
echo 2. Patient management workflow - 1000 virtual users
echo 3. Assessment screening workflow - 500 virtual users
echo 4. Assessment screening workflow - 1000 virtual users
echo 5. Report generation stress test - 500 virtual users
echo 6. Report generation stress test - 1000 virtual users
echo 7. ML prediction performance test - 500 virtual users
echo 8. ML prediction performance test - 1000 virtual users
echo 9. Patient browsing and search - 500 virtual users
echo 10. Mixed healthcare workflow - 500 virtual users
echo 11. Custom scenario
echo 12. Exit
echo.

set /p choice="Enter your choice (1-12): "

if "%choice%"=="1" (
    echo.
    echo Running Patient management workflow with 500 virtual users...
    python loadtesting/virtual_user_load_test.py --scenario "Patient management workflow" --users 500
    goto end
)

if "%choice%"=="2" (
    echo.
    echo Running Patient management workflow with 1000 virtual users...
    python loadtesting/virtual_user_load_test.py --scenario "Patient management workflow" --users 1000
    goto end
)

if "%choice%"=="3" (
    echo.
    echo Running Assessment screening workflow with 500 virtual users...
    python loadtesting/virtual_user_load_test.py --scenario "Assessment screening workflow" --users 500
    goto end
)

if "%choice%"=="4" (
    echo.
    echo Running Assessment screening workflow with 1000 virtual users...
    python loadtesting/virtual_user_load_test.py --scenario "Assessment screening workflow" --users 1000
    goto end
)

if "%choice%"=="5" (
    echo.
    echo Running Report generation stress test with 500 virtual users...
    python loadtesting/virtual_user_load_test.py --scenario "Report generation stress test" --users 500
    goto end
)

if "%choice%"=="6" (
    echo.
    echo Running Report generation stress test with 1000 virtual users...
    python loadtesting/virtual_user_load_test.py --scenario "Report generation stress test" --users 1000
    goto end
)

if "%choice%"=="7" (
    echo.
    echo Running ML prediction performance test with 500 virtual users...
    python loadtesting/virtual_user_load_test.py --scenario "ML prediction performance test" --users 500
    goto end
)

if "%choice%"=="8" (
    echo.
    echo Running ML prediction performance test with 1000 virtual users...
    python loadtesting/virtual_user_load_test.py --scenario "ML prediction performance test" --users 1000
    goto end
)

if "%choice%"=="9" (
    echo.
    echo Running Patient browsing and search with 500 virtual users...
    python loadtesting/virtual_user_load_test.py --scenario "Patient browsing and search" --users 500
    goto end
)

if "%choice%"=="10" (
    echo.
    echo Running Mixed healthcare workflow with 500 virtual users...
    python loadtesting/virtual_user_load_test.py --scenario "Mixed healthcare workflow" --users 500
    goto end
)

if "%choice%"=="11" (
    echo.
    set /p scenario="Enter scenario name: "
    set /p users="Enter number of virtual users: "
    echo.
    echo Running %scenario% with %users% virtual users...
    python loadtesting/virtual_user_load_test.py --scenario "%scenario%" --users %users%
    goto end
)

if "%choice%"=="12" (
    echo.
    echo Goodbye!
    goto end
)

echo.
echo Invalid choice. Please try again.
pause
goto start

:start
cls
goto choice

:end
echo.
echo Press any key to exit...
pause > nul