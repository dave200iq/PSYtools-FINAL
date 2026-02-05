"""Одноразовая авторизация в Telegram."""
import asyncio
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


async def main():
    cfg = load_config()
    api_id = cfg.get("api_id", "").strip()
    api_hash = cfg.get("api_hash", "").strip()
    phone = cfg.get("phone", "").strip()
    if not api_id or not api_hash:
        print("Error: fill API ID and API Hash in settings.")
        return
    if not phone:
        phone = input("Phone (e.g. +79001234567): ").strip()
    try:
        from telethon import TelegramClient
    except ImportError:
        print("Error: install telethon.")
        return
    client = TelegramClient(SESSION_PATH, int(api_id), api_hash)
    await client.start(phone=phone)
    print("\nAuthorization successful!")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
    input("\nPress Enter to exit...")
