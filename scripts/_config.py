"""Общая загрузка конфигурации для скриптов."""
import json
import os
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = Path(os.environ.get("TELEGRAM_APP_DIR", os.path.dirname(SCRIPT_DIR)))
CONFIG_PATH = str(APP_DIR / "config.json")
SESSION_PATH = str(APP_DIR / "session_export")


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_api_credentials():
    try:
        cfg = load_config()
    except (FileNotFoundError, json.JSONDecodeError):
        return 0, ""
    aid = cfg.get("api_id") or 0
    ah = (cfg.get("api_hash") or "").strip()
    try:
        return int(aid) if aid else 0, ah
    except (TypeError, ValueError):
        return 0, ""


def write_progress(phase: str, current: int, total: int):
    path = os.environ.get("PSY_PROGRESS_FILE")
    if path:
        try:
            Path(path).write_text(f"{phase}|{current}|{total}", encoding="utf-8")
        except Exception:
            pass
