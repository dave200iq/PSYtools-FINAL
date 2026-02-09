@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

set "REPO_URL=https://github.com/dave200iq/PSYtools-FINAL.git"

echo === Push to PSYtools-FINAL ===
echo Repo: %REPO_URL%
echo Folder: %cd%
echo.

git --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Git is not installed.
  echo Install Git: https://git-scm.com/download/win
  pause
  exit /b 1
)

if not exist ".git" (
  echo Initializing git...
  git init
)

echo Setting branch to main...
git branch -M main >nul 2>&1

echo Configuring origin...
git remote remove origin >nul 2>&1
git remote add origin "%REPO_URL%"

echo.
echo Adding files (respects .gitignore)...
git add .

echo.
echo Creating commit if needed...
git diff --cached --quiet
if errorlevel 1 (
  git commit -m "update"
) else (
  echo Nothing to commit.
)

echo.
echo Pushing to GitHub...
echo If prompted:
echo   Username: dave200iq
echo   Password: use your GitHub token (PAT)
git push -u origin main

echo.
echo Done. Actions:
echo   https://github.com/dave200iq/PSYtools-FINAL/actions
echo.
pause
endlocal
