@echo off
REM Quick setup script for PDF ChatBot RAG Application (Windows)

echo 🚀 PDF ChatBot RAG - Quick Setup
echo =================================

REM Check prerequisites
echo 🔍 Checking prerequisites...

docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

echo ✅ Prerequisites check passed

REM Setup environment files
echo 🔧 Setting up environment files...

if not exist "backend\.env" (
    copy "backend\.env.example" "backend\.env" >nul
    echo ✅ Backend .env file created
)

if not exist "frontend\.env.local" (
    copy "frontend\.env.local.example" "frontend\.env.local" >nul
    echo ✅ Frontend .env.local file created
)

REM Quick start
echo 🏗️ Building and starting services...

REM Pull base images first
echo 📥 Pulling base images...
docker pull python:3.11-slim
docker pull node:18-alpine

REM Build and start
docker-compose up --build -d

echo ⏳ Waiting for services to start...
timeout /t 30 /nobreak > nul

REM Check if services are running
curl -f http://localhost:8000/health >nul 2>&1
if %errorlevel%==0 (
    echo ✅ Backend is running
) else (
    echo ⚠️ Backend might still be starting...
)

curl -f http://localhost:3000 >nul 2>&1
if %errorlevel%==0 (
    echo ✅ Frontend is running
) else (
    echo ⚠️ Frontend might still be starting...
)

REM Show access info
echo.
echo 🎉 Setup completed!
echo.
echo 📋 Access your application:
echo   🌐 Frontend:      http://localhost:3000
echo   🔌 Backend API:   http://localhost:8000
echo   📚 API Docs:      http://localhost:8000/docs
echo   ❤️ Health Check:  http://localhost:8000/health
echo.
echo 🔧 Useful commands:
echo   📊 View logs:     docker-compose logs -f
echo   🛑 Stop:          docker-compose down
echo   🔄 Restart:       docker-compose restart
echo.
echo 📖 Next steps:
echo   1. Open http://localhost:3000 in your browser
echo   2. Upload a PDF document
echo   3. Start asking questions!
echo.
pause
