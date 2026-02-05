@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo === Push Mac+Windows build to GitHub ===

git add .
git status
git commit -m "Add Mac + Windows build workflow"
if errorlevel 1 git commit --allow-empty -m "Add Mac + Windows build workflow"
git push

echo.
echo Done! Open https://github.com/dave200iq/PSYtools/actions
echo Run workflow "Build (Mac + Windows)"
pause
