"""
Лицензионный сервер для Psylocyba Tools — версия для Render (PostgreSQL).
"""
import json
import os
from datetime import datetime
from pathlib import Path

from flask import Flask, request, jsonify

app = Flask(__name__)
KEYS_FILE = Path(__file__).parent / "keys.json"
DATABASE_URL = os.environ.get("DATABASE_URL")


def get_db():
    """Подключение к PostgreSQL (Render) или JSON (локально)."""
    if DATABASE_URL:
        try:
            import psycopg2
            import urllib.parse
            url = DATABASE_URL
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            return psycopg2.connect(url)
        except Exception as e:
            print(f"DB error: {e}")
            return None
    return None


def load_keys():
    """Загрузить ключи из БД или JSON."""
    conn = get_db()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT key, hwid, created FROM license_keys")
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return {r[0]: {"hwid": r[1], "created": r[2] and r[2].isoformat()} for r in rows}
        except Exception as e:
            print(f"Load error: {e}")
            if conn:
                conn.close()
            return {}
    if KEYS_FILE.exists():
        try:
            with open(KEYS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_key(key, hwid=None, first_used=None):
    """Сохранить/обновить ключ в БД."""
    conn = get_db()
    if conn:
        try:
            cur = conn.cursor()
            if first_used is not None:
                cur.execute(
                    "UPDATE license_keys SET hwid=%s, first_used=%s WHERE key=%s",
                    (hwid, first_used, key)
                )
            else:
                cur.execute(
                    "INSERT INTO license_keys (key, hwid, created) VALUES (%s, %s, %s) ON CONFLICT (key) DO NOTHING",
                    (key, None, datetime.utcnow())
                )
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Save error: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return False
    keys = load_keys()
    if first_used is not None and key in keys:
        keys[key]["hwid"] = hwid
        keys[key]["first_used"] = first_used.isoformat()
    else:
        keys[key] = {"hwid": hwid, "created": datetime.utcnow().isoformat()}
    try:
        with open(KEYS_FILE, "w", encoding="utf-8") as f:
            json.dump(keys, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def delete_key(key):
    """Удалить ключ."""
    conn = get_db()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM license_keys WHERE key=%s", (key,))
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception:
            if conn:
                conn.rollback()
                conn.close()
            return False
    keys = load_keys()
    if key in keys:
        del keys[key]
        with open(KEYS_FILE, "w", encoding="utf-8") as f:
            json.dump(keys, f, ensure_ascii=False, indent=2)
    return True


def init_db():
    """Создать таблицу при первом запуске (Render)."""
    if not DATABASE_URL:
        return
    try:
        import psycopg2
        import urllib.parse
        url = DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        conn = psycopg2.connect(url)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS license_keys (
                key VARCHAR(64) PRIMARY KEY,
                hwid VARCHAR(64),
                created TIMESTAMP,
                first_used TIMESTAMP
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Init DB: {e}")


init_db()


@app.route("/")
def index():
    return jsonify({"status": "ok", "service": "Psylocyba License Server"})


@app.route("/verify", methods=["GET"])
def verify():
    key = (request.args.get("key") or "").strip().upper().replace(" ", "-")
    hwid = (request.args.get("hwid") or "").strip()
    if not key or not hwid:
        return jsonify({"valid": False, "error": "missing_params"}), 400

    keys = load_keys()
    if key not in keys:
        return jsonify({"valid": False, "error": "invalid_key"}), 200

    entry = keys[key]
    bound_hwid = entry.get("hwid")

    if bound_hwid is None:
        entry["hwid"] = hwid
        entry["first_used"] = datetime.utcnow().isoformat()
        save_key(key, hwid, datetime.utcnow())
        return jsonify({"valid": True}), 200

    if bound_hwid != hwid:
        return jsonify({"valid": False, "error": "key_bound"}), 200

    return jsonify({"valid": True}), 200


@app.route("/add", methods=["POST"])
def add_key_route():
    key = (request.form.get("key") or request.args.get("key") or "").strip().upper().replace(" ", "-")
    if not key:
        return jsonify({"ok": False, "error": "key required"}), 400

    keys = load_keys()
    if key in keys:
        return jsonify({"ok": False, "error": "key exists"}), 200

    save_key(key, None, None)
    return jsonify({"ok": True, "key": key}), 200


@app.route("/revoke", methods=["POST"])
def revoke_key():
    key = (request.form.get("key") or request.args.get("key") or "").strip().upper()
    if key:
        delete_key(key)
    return jsonify({"ok": True}), 200


@app.route("/list", methods=["GET"])
def list_keys():
    keys = load_keys()
    return jsonify({"keys": list(keys.keys()), "details": keys}), 200
