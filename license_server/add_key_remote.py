"""Добавить ключ на облачный сервер. Использование: python add_key_remote.py URL KEY"""
import sys
import urllib.request
import urllib.parse

def main():
    if len(sys.argv) < 3:
        print("Usage: python add_key_remote.py https://user.pythonanywhere.com XXXX-XXXX-XXXX-XXXX")
        sys.exit(1)
    base = sys.argv[1].rstrip("/")
    key = " ".join(sys.argv[2:]).strip().upper().replace(" ", "-")
    url = f"{base}/add"
    data = urllib.parse.urlencode({"key": key}).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            resp = r.read().decode()
            if "ok" in resp and "true" in resp:
                print(f"Key {key} added.")
            else:
                print(resp)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
