@echo off
setlocal enabledelayedexpansion

echo Starting OralSmart deployment...
echo.

:: Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running. Please start Docker and try again.
    pause
    exit /b 1
)
echo [SUCCESS] Docker is running

:: Check if .env file exists
if not exist ".env" (
    echo [WARNING] .env file not found. Copying from .env.example
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo [WARNING] Please edit .env file with your settings before continuing
        pause
    ) else (
        echo [ERROR] .env.example file not found. Please create .env file manually.
        pause
        exit /b 1
    )
)

:: Create necessary directories
echo [INFO] Creating necessary directories...
mkdir docker\ssl 2>nul
mkdir logs 2>nul
mkdir src\media 2>nul
mkdir src\staticfiles 2>nul

:: Build and start services
echo [INFO] Building Docker images...
docker-compose build --no-cache

echo [INFO] Starting services...
docker-compose up -d

:: Wait for database to be ready
echo [INFO] Waiting for database to be ready...
timeout /t 30 /nobreak >nul

:: Run migrations
echo [INFO] Running database migrations...
docker-compose exec web python manage.py migrate

:: Create superuser if it doesn't exist
echo [INFO] Checking for superuser...
if exist "superuserDetails.txt" (
    echo [INFO] Creating superuser from superuserDetails.txt...
    docker-compose exec web python manage.py shell < superuserDetails.txt 2>nul
)

:: Load initial data if needed
if exist "src\fixtures\initial_data.json" (
    echo [INFO] Loading initial data...
    docker-compose exec web python manage.py loaddata initial_data.json
)

:: Check service health
echo [INFO] Checking service health...
timeout /t 10 /nobreak >nul

:: Show running services
echo [INFO] Current service status:
docker-compose ps

echo.
echo [SUCCESS] Deployment completed!
echo.
echo [INFO] Application URLs:
echo   Web Application: http://localhost:8000
echo   Admin Panel: http://localhost:8000/admin
echo   API Health Check: http://localhost:8000/health
echo.
echo [INFO] Useful commands:
echo   View logs: docker-compose logs -f
echo   Restart services: docker-compose restart
echo   Stop services: docker-compose down
echo   🧹 Clean up: docker-compose down -v --rmi all
echo.
echo [INFO] For production deployment, use docker-compose-prod.yml
pause
