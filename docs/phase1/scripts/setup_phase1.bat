@echo off
REM Phase 1 Setup Script for Windows

echo.
echo ========================================
echo 🚀 Starting Phase 1 - FFB Annotation Setup
echo ========================================
echo.

REM Check if Docker is installed
echo Step 1: Checking Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker not found!
    echo    Download from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo ✅ Docker found

REM Create data directory
echo.
echo Step 2: Creating Label Studio data directory...
if not exist "%USERPROFILE%\label-studio-data" mkdir "%USERPROFILE%\label-studio-data"
echo ✅ Directory created: %USERPROFILE%\label-studio-data

REM Start Label Studio
echo.
echo Step 3: Starting Label Studio (this takes ~30 seconds)...
docker run -d -p 8080:8080 -v %USERPROFILE%\label-studio-data:/label-studio/data ^
  --name label-studio ^
  heartexlabs/label-studio:latest

echo.
echo Waiting for Label Studio to start...
timeout /t 15 /nobreak

REM Check if running
docker ps | find "label-studio" >nul
if errorlevel 1 (
    echo.
    echo ❌ Label Studio failed to start. Try:
    echo    docker logs label-studio
    pause
) else (
    echo.
    echo ✅ Label Studio is running!
    echo.
    echo 🎉 SUCCESS! Label Studio is ready:
    echo    → Open: http://localhost:8080
    echo    → Default login: admin@heartex.com / password
    echo.
    echo 📋 Next steps:
    echo    1. Go to http://localhost:8080
    echo    2. Create new project: 'FFB Detection Phase 1'
    echo    3. Upload 64 images from: SG9-RW010SS-10T-40P-070326 - SMTF1/
    echo    4. Configure YOLO annotation template
    echo    5. Start annotating FFB bunches
    echo.
    echo 📝 Track progress in: PHASE1_CHECKLIST.md
    echo.
    echo Press any key to continue...
    pause
)
