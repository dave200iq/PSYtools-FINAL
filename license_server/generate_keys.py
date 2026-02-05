"""Генерация лицензионных ключей. Использование: python generate_keys.py [количество]"""
import json
import random
import string
import sys
from datetime import datetime
from pathlib import Path

KEYS_FILE = Path(__file__).parent / "keys.json"
CHARS = string.ascii_uppercase + string.digits


def gen_key():
    """Ключ формата XXXX-XXXX-XXXX-XXXX"""
    parts = []
    for _ in range(4):
        parts.append("".join(random.choices(CHARS, k=4)))
    return "-".join(parts)


def main():
    n = 1
    if len(sys.argv) > 1:
        try:
            n = max(1, min(1000, int(sys.argv[1])))
        except ValueError:
            print("Usage: python generate_keys.py [count]")
            print("Example: python generate_keys.py 10")
            sys.exit(1)

    keys = {}
    if KEYS_FILE.exists():
        with open(KEYS_FILE, "r", encoding="utf-8") as f:
            keys = json.load(f)

    generated = []
    for _ in range(n):
        while True:
            key = gen_key()
            if key not in keys:
                break
        keys[key] = {"hwid": None, "created": datetime.utcnow().isoformat()}
        generated.append(key)

    with open(KEYS_FILE, "w", encoding="utf-8") as f:
        json.dump(keys, f, ensure_ascii=False, indent=2)

    print(f"Добавлено ключей: {len(generated)}\n")
    for k in generated:
        print(k)
    print("\nКлючи сохранены в keys.json.")


if __name__ == "__main__":
    main()
