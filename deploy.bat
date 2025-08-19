@echo off
REM Windows deployment script for PDF ChatBot RAG Application

echo 🚀 Starting PDF ChatBot RAG Application Deployment...

REM Configuration
set DOMAIN=%1
if "%DOMAIN%"=="" set DOMAIN=localhost

set ENV=%2
if "%ENV%"=="" set ENV=production

set BACKUP_DIR=.\backups\%date:~10,4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set BACKUP_DIR=%BACKUP_DIR: =0%

echo 📋 Deployment Configuration:
echo   Domain: %DOMAIN%
echo   Environment: %ENV%
echo   Backup Directory: %BACKUP_DIR%

REM Create backup directory
if not exist "backups" mkdir backups
mkdir "%BACKUP_DIR%"

REM Backup data
if exist "data" (
    echo 💾 Backing up existing data...
    xcopy "data" "%BACKUP_DIR%\data\" /E /I /H /Y
    echo ✅ Data backed up to %BACKUP_DIR%
)

REM Setup environment files
echo 🔧 Setting up environment files...

if not exist "backend\.env" (
    copy "backend\.env.example" "backend\.env"
    echo ✅ Backend environment file created
)

if not exist "frontend\.env.local" (
    copy "frontend\.env.local.example" "frontend\.env.local"
    echo ✅ Frontend environment file created
)

REM Build and deploy
echo 🏗️ Building and deploying services...

REM Stop existing services
docker-compose down

REM Build and start services
if "%ENV%"=="production" (
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
) else (
    docker-compose up -d --build
)

echo ✅ Services deployed successfully

REM Wait for services to start
echo ⏳ Waiting for services to start...
timeout /t 30 /nobreak > nul

REM Verify deployment
echo 🔍 Verifying deployment...

REM Check backend health
curl -f http://localhost:8000/health > nul 2>&1
if %errorlevel%==0 (
    echo ✅ Backend is healthy
) else (
    echo ❌ Backend health check failed
    pause
    exit /b 1
)

REM Check frontend
curl -f http://localhost:3000 > nul 2>&1
if %errorlevel%==0 (
    echo ✅ Frontend is accessible
) else (
    echo ❌ Frontend check failed
    pause
    exit /b 1
)

echo ✅ Deployment verification completed

REM Create monitoring script
echo @echo off > monitor.bat
echo echo 🔍 Health Check Report - %%date%% %%time%% >> monitor.bat
echo echo ================================ >> monitor.bat
echo curl -f http://localhost:8000/health ^>nul 2^>^&1 >> monitor.bat
echo if %%errorlevel%%==0 ^( >> monitor.bat
echo     echo ✅ Backend is healthy >> monitor.bat
echo ^) else ^( >> monitor.bat
echo     echo ❌ Backend is down >> monitor.bat
echo ^) >> monitor.bat
echo curl -f http://localhost:3000 ^>nul 2^>^&1 >> monitor.bat
echo if %%errorlevel%%==0 ^( >> monitor.bat
echo     echo ✅ Frontend is healthy >> monitor.bat
echo ^) else ^( >> monitor.bat
echo     echo ❌ Frontend is down >> monitor.bat
echo ^) >> monitor.bat
echo echo. >> monitor.bat
echo echo 📊 Docker Status: >> monitor.bat
echo docker-compose ps >> monitor.bat

echo 📊 Monitoring script created (monitor.bat)

REM Show deployment info
echo.
echo 🎉 Deployment completed successfully!
echo.
echo 📋 Access Information:
echo   Frontend:      http://%DOMAIN%:3000
echo   Backend API:   http://%DOMAIN%:8000
echo   API Docs:      http://%DOMAIN%:8000/docs
echo   Health Check:  http://%DOMAIN%:8000/health
echo.
echo 🔧 Management Commands:
echo   View logs:     docker-compose logs -f
echo   Stop services: docker-compose down
echo   Restart:       docker-compose restart
echo   Monitor:       monitor.bat
echo.
echo 💾 Backup Location: %BACKUP_DIR%
echo.
pause
