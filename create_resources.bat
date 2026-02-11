@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Creating assets...
python -m pip install Pillow -q 2>nul
python create_assets.py
pause
