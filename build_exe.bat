@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Building Psylocyba Tools...
python -m pip install -q pyinstaller customtkinter telethon
python build_exe.py
if exist "dist\Psylocyba_Tools.exe" (echo. & echo Done! dist\Psylocyba_Tools.exe) else (echo Build failed.)
pause
