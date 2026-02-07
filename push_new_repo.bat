@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo === Psylocyba Tools - Push to NEW GitHub repo ===
echo.

git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git is not installed.
    echo Install Git: https://git-scm.com/download/win
    echo Then re-run this script.
    pause
    exit /b 1
)

set /p REPO_URL=Enter new repo URL (https://github.com/USER/REPO.git): 
if "%REPO_URL%"=="" (
    echo [ERROR] Repo URL is empty.
    pause
    exit /b 1
)

echo.
set /p GH_TOKEN=Optional: enter GitHub token (press Enter to skip): 

if not exist ".git" (
    echo Initializing git...
    git init
)

echo.
echo Adding files (respects .gitignore)...
git add .

echo.
echo Creating commit...
git commit -m "init"
if errorlevel 1 (
    echo No changes to commit - continuing.
)

echo.
echo Setting branch to main...
git branch -M main

echo.
echo Setting remote...
git remote remove origin 2>nul

if "%GH_TOKEN%"=="" (
    git remote add origin %REPO_URL%
) else (
    rem Insert token into URL only for this push, then reset to clean URL
    set TOKEN_URL=%REPO_URL:https://=https://%GH_TOKEN%@%
    git remote add origin %TOKEN_URL%
)

echo.
echo Pushing...
git push -u origin main

if not "%GH_TOKEN%"=="" (
    git remote set-url origin %REPO_URL%
)

set GH_TOKEN=
set TOKEN_URL=

echo.
echo Done.
pause
@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo === Psylocyba Tools - Push to NEW GitHub repo ===
echo.

git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git is not installed.
    echo Install Git: https://git-scm.com/download/win
    echo Then re-run this script.
    pause
    exit /b 1
)

set /p REPO_URL=Enter new repo URL (https://github.com/USER/REPO.git): 
if "%REPO_URL%"=="" (
    echo [ERROR] Repo URL is empty.
    pause
    exit /b 1
)

echo.
set /p GH_TOKEN=Optional: enter GitHub token (press Enter to skip): 

if not exist ".git" (
    echo Initializing git...
    git init
)

echo.
echo Adding files (respects .gitignore)...
git add .

echo.
echo Creating commit...
git commit -m "init"
if errorlevel 1 (
    echo No changes to commit - continuing.
)

echo.
echo Setting branch to main...
git branch -M main

echo.
echo Setting remote...
git remote remove origin 2>nul

if "%GH_TOKEN%"=="" (
    git remote add origin %REPO_URL%
) else (
    rem Insert token into URL only for this push, then reset to clean URL
    set TOKEN_URL=%REPO_URL:https://=https://%GH_TOKEN%@%
    git remote add origin %TOKEN_URL%
)

echo.
echo Pushing...
git push -u origin main

if not "%GH_TOKEN%"=="" (
    git remote set-url origin %REPO_URL%
)

set GH_TOKEN=
set TOKEN_URL=

echo.
echo Done.
pause
