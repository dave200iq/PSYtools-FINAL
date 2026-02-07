@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo === Psylocyba Tools - Push to NEW GitHub repo ===
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

echo 5. Repo URL...
set /p REPO_URL=Enter new repo URL (https://github.com/USER/REPO.git): 
if "%REPO_URL%"=="" (
    echo.
    echo [ERROR] Repo URL is empty.
    pause
    exit /b 1
)
echo.

echo 6. Optional token...
set /p GH_TOKEN=Optional: enter GitHub token (press Enter to skip): 
echo.

echo 7. Connecting to GitHub...
git remote remove origin 2>nul
if "%GH_TOKEN%"=="" (
    git remote add origin "%REPO_URL%"
) else (
    rem Insert token into URL only for this push, then reset to clean URL
    rem GitHub PAT should be used as password; username can be x-access-token
    set TOKEN_URL=%REPO_URL:https://=https://x-access-token:%GH_TOKEN%@%
    git remote add origin "%TOKEN_URL%"
)
echo.

echo 8. Pushing to GitHub...
echo    (If no token, you may be asked to log in)
git push -u origin main
echo.

if errorlevel 1 (
    echo.
    echo [ERROR] Push failed. You may need to log in to GitHub.
    echo Try: git push -u origin main
) else (
    if not "%GH_TOKEN%"=="" (
        git remote set-url origin "%REPO_URL%"
    )
    set GH_TOKEN=
    set TOKEN_URL=
    echo.
    echo === Done! ===
    echo Open your repo on GitHub - go to Actions - run Build (Mac + Windows).
)

echo.
pause
