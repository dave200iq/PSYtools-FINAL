@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Creating assets (fonts, icons, flags)...
python -m pip install Pillow -q 2>nul
python create_assets.py
echo.
pause
