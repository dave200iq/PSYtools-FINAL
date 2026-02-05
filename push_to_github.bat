@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo === Psylocyba Tools - Push to GitHub ===
echo.

git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git is not installed!
    echo.
    echo Install Git from: https://git-scm.com/download/win
    echo After installation, restart the terminal and run this script again.
    pause
    exit /b 1
)

if not exist ".git" (
    echo 1. Initializing Git...
    git init
    echo.
)

echo 2. Adding files...
git add .
echo.

echo 3. Creating commit...
git commit -m "first commit"
echo.

echo 4. Setting branch to main...
git branch -M main
echo.

echo 5. Connecting to GitHub...
git remote remove origin 2>nul
git remote add origin https://github.com/dave200iq/PSYtools.git
echo.

echo 6. Pushing to GitHub...
echo    (You may be asked to log in to GitHub)
git push -u origin main
echo.

if errorlevel 1 (
    echo.
    echo [ERROR] Push failed. You may need to log in to GitHub.
    echo Try: git push -u origin main
) else (
    echo.
    echo === Done! ===
    echo Open https://github.com/dave200iq/PSYtools - go to Actions - wait for Mac build.
)

echo.
pause
