@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === Лицензионный сервер Psylocyba Tools ===
echo.

if not exist "keys.json" (
    echo keys.json не найден, создаём...
    python -c "import json; open('keys.json','w').write('{}')"
)

echo Установка Flask...
python -m pip install flask -q
if errorlevel 1 (
    echo Ошибка установки. Выполните вручную: python -m pip install flask
    pause
    exit /b 1
)
echo.
echo Запуск на http://0.0.0.0:5000
echo Добавить ключ: python add_key.py XXXX-XXXX-XXXX
echo Закройте окно для остановки.
echo.
python server.py
pause
