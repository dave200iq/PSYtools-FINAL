"""
Лицензионный сервер для Psylocyba Tools.
Запуск: python server.py
Порт по умолчанию: 5000
"""
import json
import os
from datetime import datetime
from pathlib import Path

from flask import Flask, request, jsonify

app = Flask(__name__)
KEYS_FILE = Path(__file__).parent / "keys.json"


def load_keys():
    if not KEYS_FILE.exists():
        return {}
    try:
        with open(KEYS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_keys(data):
    with open(KEYS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@app.route("/")
def index():
    return jsonify({"status": "ok", "service": "Psylocyba License Server"})


@app.route("/verify", methods=["GET"])
def verify():
    """Проверка ключа: GET /verify?key=XXX&hwid=YYY"""
    key = (request.args.get("key") or "").strip().upper()
    hwid = (request.args.get("hwid") or "").strip()

    if not key or not hwid:
        return jsonify({"valid": False, "error": "missing_params"}), 400

    keys = load_keys()
    if key not in keys:
        return jsonify({"valid": False, "error": "invalid_key"}), 200

    entry = keys[key]
    bound_hwid = entry.get("hwid")

    if bound_hwid is None:
        # Первое использование — привязываем к этому компьютеру
        entry["hwid"] = hwid
        entry["first_used"] = datetime.utcnow().isoformat()
        keys[key] = entry
        save_keys(keys)
        return jsonify({"valid": True}), 200

    if bound_hwid != hwid:
        # Ключ привязан к другому компьютеру
        return jsonify({"valid": False, "error": "key_bound"}), 200

    return jsonify({"valid": True}), 200


@app.route("/add", methods=["POST"])
def add_key():
    """Добавить ключ (для админа). POST с form: key=XXX"""
    key = (request.form.get("key") or request.args.get("key") or "").strip().upper()
    if not key:
        return jsonify({"ok": False, "error": "key required"}), 400

    keys = load_keys()
    if key in keys:
        return jsonify({"ok": False, "error": "key exists"}), 200

    keys[key] = {"hwid": None, "created": datetime.utcnow().isoformat()}
    save_keys(keys)
    return jsonify({"ok": True, "key": key}), 200


@app.route("/revoke", methods=["POST"])
def revoke_key():
    """Отозвать ключ. POST: key=XXX"""
    key = (request.form.get("key") or request.args.get("key") or "").strip().upper()
    if not key:
        return jsonify({"ok": False, "error": "key required"}), 400

    keys = load_keys()
    if key in keys:
        del keys[key]
        save_keys(keys)
    return jsonify({"ok": True}), 200


@app.route("/list", methods=["GET"])
def list_keys():
    """Список ключей (для админа)"""
    keys = load_keys()
    return jsonify({"keys": list(keys.keys()), "details": keys}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"License server: http://0.0.0.0:{port}")
    print("Endpoints: /verify?key=&hwid=  /add  /revoke  /list")
    app.run(host="0.0.0.0", port=port)
