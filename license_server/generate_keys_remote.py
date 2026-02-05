"""Генерация ключей и добавление на облачный сервер.
Использование: python generate_keys_remote.py URL [количество]

Пример: python generate_keys_remote.py https://tmprrstsfctn.pythonanywhere.com 5
"""
import random
import string
import sys
import urllib.request
import urllib.parse

CHARS = string.ascii_uppercase + string.digits


def gen_key():
    parts = []
    for _ in range(4):
        parts.append("".join(random.choices(CHARS, k=4)))
    return "-".join(parts)


def add_key(base_url, key):
    url = f"{base_url.rstrip('/')}/add"
    data = urllib.parse.urlencode({"key": key}).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=30) as r:
        resp = r.read().decode()
        return "ok" in resp and "true" in resp


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_keys_remote.py https://user.pythonanywhere.com [count]")
        print("Example: python generate_keys_remote.py https://tmprrstsfctn.pythonanywhere.com 10")
        sys.exit(1)

    base = sys.argv[1].rstrip("/")
    n = 1
    if len(sys.argv) > 2:
        try:
            n = max(1, min(100, int(sys.argv[2])))
        except ValueError:
            pass

    print(f"Генерация {n} ключей...\n")
    for i in range(n):
        key = gen_key()
        try:
            if add_key(base, key):
                print(key)
            else:
                print(f"{key} — ошибка (возможно, уже есть)")
        except Exception as e:
            print(f"{key} — ошибка: {e}")
    print("\nГотово.")


if __name__ == "__main__":
    main()
