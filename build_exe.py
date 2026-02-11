"""Сборка Psylocyba Tools в .exe"""
import subprocess
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
config_path = APP_DIR / "config.json"
if not config_path.exists():
    config_path.write_text('{"api_id":"","api_hash":"","phone":"","session_name":"session_export","lang":"ru"}', encoding="utf-8")

dist_exe = APP_DIR / "dist" / "Psylocyba_Tools.exe"
print("Building Psylocyba_Tools.exe...")
print("Working dir:", APP_DIR)
print("Output will be:", dist_exe)
print()
result = subprocess.run(
    [sys.executable, "-m", "PyInstaller", "--noconfirm", "Psylocyba_Tools.spec"],
    cwd=str(APP_DIR),
)
if result.returncode == 0 and dist_exe.exists():
    print("\nDone!", dist_exe)
else:
    print("\nBuild failed.")
    print("Expected file:", dist_exe)
    if (APP_DIR / "build").exists():
        print("(Folder 'build' exists — PyInstaller ran but exe step may have failed. Check errors above or antivirus.)")
    sys.exit(1)
