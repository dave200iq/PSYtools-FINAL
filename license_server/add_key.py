"""Добавить лицензионный ключ. Использование: python add_key.py ABCD-EFGH-IJKL-MNOP"""
import json
import sys
from datetime import datetime
from pathlib import Path

KEYS_FILE = Path(__file__).parent / "keys.json"


def main():
    key = " ".join(sys.argv[1:]).strip().upper().replace(" ", "-")
    if not key:
        print("Usage: python add_key.py YOUR-KEY")
        sys.exit(1)

    keys = {}
    if KEYS_FILE.exists():
        with open(KEYS_FILE, "r", encoding="utf-8") as f:
            keys = json.load(f)

    if key in keys:
        print(f"Key {key} already exists.")
        sys.exit(0)

    keys[key] = {"hwid": None, "created": datetime.utcnow().isoformat()}
    with open(KEYS_FILE, "w", encoding="utf-8") as f:
        json.dump(keys, f, ensure_ascii=False, indent=2)
    print(f"Added key: {key}")


if __name__ == "__main__":
    main()
