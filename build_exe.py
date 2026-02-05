"""Сборка Psylocyba Tools в .exe"""
import subprocess
import sys
from pathlib import Path

APP_DIR = Path(__file__).parent
config_path = APP_DIR / "config.json"
if not config_path.exists():
    config_path.write_text('{"api_id":"","api_hash":"","phone":"","session_name":"session_export","lang":"ru"}', encoding="utf-8")

print("Building Psylocyba_Tools.exe...")
result = subprocess.run(
    [sys.executable, "-m", "PyInstaller", "--noconfirm", "Psylocyba_Tools.spec"],
    cwd=str(APP_DIR),
)
if result.returncode == 0 and (APP_DIR / "dist" / "Psylocyba_Tools.exe").exists():
    print("\nDone! dist/Psylocyba_Tools.exe")
else:
    print("\nBuild failed.")
    sys.exit(1)
