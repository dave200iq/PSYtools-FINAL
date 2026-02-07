"""
Psylocyba Tools — современный кислотный дизайн, EN/RU, анимации.
"""
import os
import sys
import json
import webbrowser
import subprocess
import threading
import asyncio
import hashlib
import platform
import uuid
from pathlib import Path
import ssl
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import quote

TELEGRAM_CHANNEL_URL = "https://t.me/+A0Qr2usbsX41YmJi"

# URL лицензионного сервера. Замените на https://ваш-сервер.com перед сборкой exe.
# Поставьте "skip" для отключения проверки (только для разработки).
LICENSE_SERVER_URL = "https://psylocyba-license.onrender.com"

def get_app_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent

APP_DIR = get_app_dir()
SCRIPTS_DIR = APP_DIR / "scripts"

# На Mac в .app нельзя писать файлы — конфиг, лицензия и результаты в папку пользователя
if sys.platform == "darwin" and getattr(sys, "frozen", False):
    try:
        _user_data = Path.home() / "Library" / "Application Support" / "Psylocyba_Tools"
        _user_data.mkdir(parents=True, exist_ok=True)
        # Проверяем, что реально можно записать
        _test_file = _user_data / ".write_test"
        _test_file.write_text("ok", encoding="utf-8")
        _test_file.unlink()
        USER_DATA_DIR = _user_data
    except Exception:
        USER_DATA_DIR = Path.home() / "Desktop"
else:
    USER_DATA_DIR = APP_DIR

CONFIG_PATH = USER_DATA_DIR / "config.json"
LICENSE_PATH = USER_DATA_DIR / ".license"

# На macOS без этого SSL-подключение (в т.ч. Telethon) может молча падать
if sys.platform == "darwin":
    try:
        import certifi
        os.environ.setdefault("SSL_CERT_FILE", certifi.where())
        os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
    except Exception:
        pass


def get_hwid():
    """Идентификатор компьютера для привязки ключа."""
    s = f"{platform.node()}-{uuid.getnode()}"
    return hashlib.sha256(s.encode()).hexdigest()[:32]


def load_license():
    try:
        with open(LICENSE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_license(key):
    with open(LICENSE_PATH, "w", encoding="utf-8") as f:
        json.dump({"key": key.strip().upper().replace(" ", "-")}, f)


def clear_license():
    try:
        if LICENSE_PATH.exists():
            LICENSE_PATH.unlink()
    except Exception:
        pass


def _make_ssl_context():
    """SSL-контекст с certifi для Mac и других платформ."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def verify_license(key, hwid):
    """Проверка ключа на сервере. Возвращает (True, None) или (False, error_message)."""
    if not key or not hwid:
        return False, "invalid"
    key = key.strip().upper().replace(" ", "-")
    url = f"{LICENSE_SERVER_URL.rstrip('/')}/verify?key={quote(key)}&hwid={quote(hwid)}"
    import time
    ctx = _make_ssl_context()
    for attempt in range(3):
        try:
            req = Request(url, headers={"User-Agent": "PsylocybaTools/1.0"})
            with urlopen(req, timeout=90, context=ctx) as r:
                data = json.loads(r.read().decode())
                if data.get("valid"):
                    return True, None
                return False, data.get("error", "invalid")
        except (URLError, HTTPError, json.JSONDecodeError, OSError):
            if attempt < 2:
                time.sleep(5)
            else:
                return False, "network"


def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"api_id": "", "api_hash": "", "phone": "", "session_name": "session_export", "lang": "ru"}


def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def install_deps():
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(APP_DIR / "requirements.txt"), "-q"],
            check=True, cwd=str(APP_DIR),
        )
        return True
    except subprocess.CalledProcessError:
        return False


class LogWriter:
    def __init__(self, widget, root):
        self.widget = widget
        self.root = root

    def write(self, s):
        if s.strip():
            def _update():
                self.widget.insert("end", s)
                self.widget.see("end")
            self.root.after(0, _update)

    def flush(self):
        pass


def run_script_in_process(script_name: str, args: list, log_widget, root, on_done=None, on_error=None):
    if getattr(sys, "frozen", False):
        scripts_path = Path(sys._MEIPASS) / "scripts"
    else:
        scripts_path = SCRIPTS_DIR
    if not (scripts_path / script_name).exists() and not getattr(sys, "frozen", False):
        log_widget.insert("end", f"Error: {script_name} not found\n")
        if on_error:
            root.after(0, lambda: on_error(str(script_name) + " not found"))
        return
    log_widget.delete("1.0", "end")
    log_widget.insert("end", f"Run: {script_name}\n\n")

    def run():
        os.environ["TELEGRAM_APP_DIR"] = str(USER_DATA_DIR)
        sys.path.insert(0, str(scripts_path))
        old_stdout = sys.stdout
        try:
            sys.stdout = LogWriter(log_widget, root)
            if script_name == "telegram_export_members.py":
                from telegram_export_members import run_export
                asyncio.run(run_export(args[1], args[3]))
            elif script_name == "telegram_clone_group.py":
                from telegram_clone_group import main as clone_main
                asyncio.run(clone_main(args[1], args[3]))
            elif script_name == "telegram_clone_channel.py":
                from telegram_clone_channel import main as clone_main
                asyncio.run(clone_main(args[1], args[3]))
            if on_done:
                root.after(0, on_done)
        except Exception as e:
            root.after(0, lambda: log_widget.insert("end", f"\nError: {e}\n"))
            if on_error:
                root.after(0, lambda: on_error(str(e)))
        finally:
            sys.stdout = old_stdout
            root.after(0, lambda: log_widget.insert("end", "\n\nDone.\n"))
    threading.Thread(target=run, daemon=True).start()


PROGRESS_FILE = USER_DATA_DIR / ".progress"

def run_script_subprocess_cmd(cmd: list, log_widget, root, proc_holder=None, on_done=None, on_error=None, progress_path=None, on_finish=None):
    log_widget.delete("1.0", "end")
    log_widget.insert("end", f"Run: {' '.join(cmd)}\n\n")

    def run():
        proc = None
        collected = []
        try:
            env = {**os.environ, "TELEGRAM_APP_DIR": str(USER_DATA_DIR), "PYTHONIOENCODING": "utf-8"}
            if progress_path:
                env["PSY_PROGRESS_FILE"] = str(progress_path)
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                cwd=str(USER_DATA_DIR), text=True, encoding="utf-8", errors="replace", env=env,
            )
            if proc_holder is not None:
                proc_holder.append(proc)
            for line in proc.stdout:
                collected.append(line)
                def _add(l=line):
                    log_widget.insert("end", l)
                    log_widget.see("end")
                root.after(0, _add)
            proc.wait()
            if proc.returncode == 0 and on_done:
                root.after(0, on_done)
            elif proc.returncode != 0 and proc.returncode is not None and on_error:
                err_detail = None
                for s in reversed(collected):
                    s = (s or "").strip()
                    if s.startswith("Error:") or s.startswith("Error "):
                        err_detail = s
                        break
                if not err_detail and collected:
                    err_detail = (collected[-1] or "").strip() or f"Exit code {proc.returncode}"
                else:
                    err_detail = err_detail or f"Exit code {proc.returncode}"
                root.after(0, lambda: on_error(err_detail))
            root.after(0, lambda: log_widget.insert("end", "\n\nDone.\n"))
        except Exception as e:
            root.after(0, lambda: log_widget.insert("end", f"\nError: {e}\n"))
            if on_error:
                root.after(0, lambda: on_error(str(e)))
        finally:
            if proc_holder and proc is not None and proc in proc_holder:
                try:
                    proc_holder.remove(proc)
                except ValueError:
                    pass
            if progress_path and Path(progress_path).exists():
                try:
                    Path(progress_path).unlink()
                except Exception:
                    pass
            if on_finish:
                root.after(0, on_finish)
    threading.Thread(target=run, daemon=True).start()


def run_script(script_name: str, args: list, log_widget, root, proc_holder=None, on_done=None, on_error=None, progress_path=None, on_finish=None):
    if getattr(sys, "frozen", False):
        cmd = [sys.executable, "--script", script_name] + args
    else:
        script_path = SCRIPTS_DIR / script_name
        cmd = [sys.executable, str(script_path)] + args
    run_script_subprocess_cmd(cmd, log_widget, root, proc_holder=proc_holder, on_done=on_done, on_error=on_error, progress_path=progress_path, on_finish=on_finish)


def _ask_string_inline(root, queue, prompt, secret=False):
    """Встроенный диалог CTkToplevel — всё внутри приложения, без внешних окон."""
    try:
        import customtkinter as ctk
        result = [""]
        top = ctk.CTkToplevel(root)
        top.title("Telegram")
        top.geometry("440x160")
        top.transient(root)
        top.grab_set()
        top.configure(fg_color="#100816")
        top.lift()
        top.focus_force()
        ctk.CTkLabel(top, text=prompt, font=ctk.CTkFont(size=14),
                     text_color="#00ffe8").pack(pady=(24, 10), padx=24, anchor="w")
        entry = ctk.CTkEntry(top, width=380, height=44, show="•" if secret else "",
                             fg_color="#0c0812", font=ctk.CTkFont(size=14))
        entry.pack(pady=(0, 20), padx=24)
        entry.focus()

        def on_ok():
            result[0] = entry.get().strip()
            top.destroy()

        def on_cancel():
            result[0] = ""
            top.destroy()

        btn_frame = ctk.CTkFrame(top, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(0, 20))
        ctk.CTkButton(btn_frame, text="OK", command=on_ok, width=110, height=38,
                      fg_color="#00ff88", text_color="#000").pack(side="right", padx=(10, 0))
        ctk.CTkButton(btn_frame, text="Cancel", command=on_cancel, width=110, height=38).pack(side="right")
        entry.bind("<Return>", lambda e: on_ok())
        top.after(100, entry.focus)
        top.wait_window()
        queue.append(result[0])
    except Exception:
        queue.append("")


def _show_message_inline(root, msg, is_error=False):
    """Показать уведомление/ошибку внутри приложения (CTkToplevel)."""
    try:
        import customtkinter as ctk
        top = ctk.CTkToplevel(root)
        top.title("Error" if is_error else "OK")
        top.geometry("420x120")
        top.transient(root)
        top.grab_set()
        top.configure(fg_color="#100816")
        top.lift()
        color = "#ff4466" if is_error else "#00ff88"
        ctk.CTkLabel(top, text=msg, font=ctk.CTkFont(size=13),
                     text_color=color, wraplength=360).pack(pady=24, padx=24, fill="x")
        ctk.CTkButton(top, text="OK", command=top.destroy, width=100, height=36,
                      fg_color=color, text_color="#000").pack(pady=(0, 24))
    except Exception:
        pass


def _run_auth_gui(root, log_widget):
    """Авторизация в основном окне с GUI-диалогом (без sys.stdin)."""
    cfg = load_config()
    api_id = cfg.get("api_id", "").strip()
    api_hash = cfg.get("api_hash", "").strip()
    phone = cfg.get("phone", "").strip()
    if not api_id or not api_hash:
        _show_auth_error(root, cfg.get("lang") == "ru", "api")
        return
    if not phone:
        _show_auth_error(root, cfg.get("lang") == "ru", "phone")
        return

    # Отладка: проверить, что обработчик кнопки вообще сработал
    try:
        log_widget.delete("1.0", "end")
        log_widget.insert("end", "[DEBUG] Auth button clicked, starting...\n")
        log_widget.update_idletasks()
    except Exception:
        pass

    def _notify_success(msg):
        try:
            if sys.platform == "darwin":
                root.after(0, lambda: _show_message_inline(root, msg, is_error=False))
            else:
                from tkinter import messagebox
                root.after(0, lambda: messagebox.showinfo("", msg))
        except Exception:
            pass

    def _notify_error(msg):
        try:
            if sys.platform == "darwin":
                root.after(0, lambda: _show_message_inline(root, msg, is_error=True))
            else:
                from tkinter import messagebox
                root.after(0, lambda: messagebox.showerror("", msg))
        except Exception:
            pass

    code_queue = []
    pwd_queue = []

    def _ask_code_tk():
        msg = "Код из Telegram:" if cfg.get("lang") == "ru" else "Code from Telegram:"
        _ask_string_inline(root, code_queue, msg, secret=False)

    def _ask_password_tk():
        msg = "Пароль 2FA:" if cfg.get("lang") == "ru" else "2FA password:"
        _ask_string_inline(root, pwd_queue, msg, secret=True)

    async def _auth_task():
        root.after(0, lambda: log_widget.insert("end", "[DEBUG] _auth_task started\n"))
        os.environ["TELEGRAM_APP_DIR"] = str(USER_DATA_DIR)
        if sys.platform == "darwin":
            try:
                import certifi
                os.environ["SSL_CERT_FILE"] = certifi.where()
                os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
                # Telethon использует ssl.create_default_context() без cafile — на Mac без certifi падает
                _orig_ssl = ssl.create_default_context
                def _ssl_with_certifi(**kwargs):
                    if "cafile" not in kwargs:
                        kwargs = dict(kwargs)
                        kwargs["cafile"] = certifi.where()
                    return _orig_ssl(**kwargs)
                ssl.create_default_context = _ssl_with_certifi
            except Exception:
                pass
        try:
            from telethon import TelegramClient
        except ImportError:
            root.after(0, lambda: log_widget.insert("end", "Error: install telethon.\n"))
            _notify_error("Установите telethon." if cfg.get("lang") == "ru" else "Install telethon.")
            return
        session_path = str(USER_DATA_DIR / "session_export")
        client = TelegramClient(session_path, int(api_id), api_hash)

        def code_callback():
            code_queue.clear()
            root.after(0, _ask_code_tk)
            import time
            while not code_queue:
                time.sleep(0.1)
            return code_queue[0]

        def password_callback():
            pwd_queue.clear()
            root.after(0, _ask_password_tk)
            import time
            while not pwd_queue:
                time.sleep(0.1)
            return pwd_queue[0]

        try:
            root.after(0, lambda: log_widget.insert("end", "Connecting...\n"))
            await client.connect()
            await client.start(phone=phone, code_callback=code_callback, password=password_callback)
            root.after(0, lambda: log_widget.insert("end", "Authorization successful!\n"))
            _notify_success("Успешная авторизация!" if cfg.get("lang") == "ru" else "Authorization successful!")
        except Exception as e:
            root.after(0, lambda: log_widget.insert("end", f"Error: {e}\n"))
            _notify_error(f"{'Ошибка авторизации' if cfg.get('lang') == 'ru' else 'Authorization failed'}: {e}")
        finally:
            await client.disconnect()

    def run():
        import time
        try:
            root.after(0, lambda: log_widget.insert("end", "[DEBUG] Thread started\n"))
            time.sleep(0.1)
            root.after(0, lambda: log_widget.insert("end", "Authorization...\n"))
            time.sleep(0.3)  # дать GUI обновиться
            if sys.platform == "darwin":
                # На Mac явный event loop в потоке избегает проблем с asyncio
                root.after(0, lambda: log_widget.insert("end", "[DEBUG] Creating event loop on darwin\n"))
                time.sleep(0.1)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                root.after(0, lambda: log_widget.insert("end", "[DEBUG] Running auth task\n"))
                time.sleep(0.1)
                try:
                    loop.run_until_complete(_auth_task())
                finally:
                    loop.close()
            else:
                asyncio.run(_auth_task())
            root.after(0, lambda: log_widget.insert("end", "\nDone.\n"))
        except Exception as e:
            import traceback
            err_msg = str(e)
            tb = traceback.format_exc()
            root.after(0, lambda: log_widget.insert("end", f"[DEBUG] Exception in thread:\n{tb}\n"))
            _notify_error(
                f"{'Ошибка авторизации' if cfg.get('lang') == 'ru' else 'Authorization failed'}: {err_msg}"
            )

    threading.Thread(target=run, daemon=True).start()


def _show_auth_error(root, is_ru, kind):
    """Показать ошибку валидации (API/phone). На Mac — встроенное окно, иначе messagebox."""
    if kind == "api":
        msg = "Заполните API ID и API Hash в настройках." if is_ru else "Fill API ID and API Hash in settings."
    else:
        msg = "Введите номер телефона в настройках." if is_ru else "Enter phone number in settings."
    if sys.platform == "darwin":
        _show_message_inline(root, msg, is_error=True)
    else:
        try:
            from tkinter import messagebox
            messagebox.showerror("", msg)
        except Exception:
            pass


def run_auth(root, log_widget=None):
    if log_widget is not None:
        _run_auth_gui(root, log_widget)
    else:
        try:
            from tkinter import messagebox
            messagebox.showinfo("", "Fill API settings and try again.")
        except Exception:
            pass


def animate_fade_in(window, steps=25, delay=12):
    """Плавное появление окна."""
    def step(n=0):
        if n <= steps:
            try:
                # Плавная кривая (ease-out)
                t = n / steps
                alpha = 1 - (1 - t) ** 2
                window.attributes("-alpha", min(1.0, alpha))
            except Exception:
                pass
            if n < steps:
                window.after(delay, lambda n=n: step(n + 1))
    try:
        window.attributes("-alpha", 0.0)
        window.after(20, lambda: step(0))
    except Exception:
        pass


# === TRANSLATIONS ===
LANG = {
    "ru": {
        "title": "Psylocyba Tools",
        "subtitle": "Клонирование групп и каналов · Экспорт подписчиков",
        "api_settings": "Настройки API",
        "api_hint": "API ID и Hash — см. инструкцию ниже",
        "api_id": "API ID",
        "api_hash": "API Hash",
        "phone": "Телефон",
        "phone_hint": "Через + (напр. +79001234567)",
        "save": "Сохранить",
        "install_deps": "Установить зависимости",
        "auth": "Авторизация",
        "help_api": "? Как получить API",
        "clone_group": "Клонировать группу",
        "clone_channel": "Клонировать канал",
        "export": "Экспорт подписчиков",
        "link_group": "Ссылка или @username группы:",
        "name_group": "Название новой группы (пусто = как у исходной):",
        "run_clone_group": "Запустить клонирование",
        "link_channel": "Ссылка или @username канала:",
        "name_channel": "Название нового канала (пусто = как у исходного):",
        "link_export": "Ссылка или @username канала/чата:",
        "file_save": "Файл для сохранения:",
        "browse": "Обзор...",
        "run_export": "Запустить экспорт",
        "log": "Лог выполнения",
        "saved": "Настройки сохранены.",
        "done": "Зависимости установлены.",
        "err_install": "Ошибка установки.",
        "enter_link_group": "Введите ссылку на группу.",
        "enter_link_channel": "Введите ссылку на канал.",
        "enter_link_export": "Введите ссылку на канал/чат.",
        "lang": "Язык",
        "select_lang": "Выберите язык",
        "close": "Закрыть",
        "auth_success": "Успешная авторизация!",
        "auth_err": "Ошибка авторизации.",
        "clone_success": "Клонирование завершено успешно.",
        "clone_err": "Ошибка при клонировании.",
        "export_success": "Экспорт завершён успешно.",
        "export_err": "Ошибка при экспорте.",
        "stop": "Стоп",
        "stop_confirm": "Остановка прервёт копирование/экспорт. Продолжить?",
        "stop_confirm2": "Точно остановить?",
        "stopped": "Остановлено.",
        "no_scripts": "Нет запущенных скриптов.",
        "stop_no_exe": "Остановка недоступна в exe-режиме.",
        "progress_collecting": "Сбор сообщений: {n}",
        "progress_copying": "Копирование: {cur} / {total}",
        "progress_exporting": "Экспорт: {n}",
        "license_title": "Лицензия",
        "license_enter": "Введите лицензионный ключ:",
        "license_activate": "Активировать (или Enter)",
        "license_invalid": "Неверный ключ.",
        "license_bound": "Ключ привязан к другому компьютеру.",
        "license_network": "Сервер недоступен. Подождите минуту и попробуйте снова.",
        "mass_send": "Массовая рассылка",
        "stats": "Статистика",
        "link_mass": "Ссылка канала/группы:",
        "message_text": "Текст сообщения:",
        "delay_sec": "Задержка между сообщениями (сек):",
        "run_mass_send": "Запустить рассылку",
        "mass_success": "Рассылка завершена.",
        "mass_err": "Ошибка рассылки.",
        "link_stats": "Ссылка канала/группы:",
        "run_stats": "Получить статистику",
        "stats_success": "Статистика получена.",
        "stats_err": "Ошибка получения статистики.",
        "export_format": "Формат экспорта:",
        "export_include_bots": "Включать ботов",
        "check_log_hint": "Проверьте лог ниже для деталей.",
        "help_clone_group": "КЛОНИРОВАНИЕ ГРУППЫ\n\nКак работает: создаётся новая группа, копируются аватар, описание и все сообщения (включая топики форума).\n\nПрава: достаточно быть участником исходной группы. Админ не нужен.",
        "help_clone_channel": "КЛОНИРОВАНИЕ КАНАЛА\n\nКак работает: создаётся новый канал, копируются аватар, описание и все посты с медиа.\n\nПрава: достаточно быть подписчиком исходного канала. Админ не нужен.",
        "help_export": "ЭКСПОРТ ПОДПИСЧИКОВ\n\nКак работает: собирает список участников канала/группы и сохраняет в файл (ID, имя, @username в выбранном формате). Боты по умолчанию исключаются.\n\nПрава: нужны права администратора в канале или группе.",
        "help_mass_send": "МАССОВАЯ РАССЫЛКА\n\nКак работает: получает список участников, затем отправляет каждому личное сообщение (в ЛС) с заданной задержкой. Боты и удалённые аккаунты пропускаются.\n\nПрава: нужны права администратора в канале или группе.",
        "help_stats": "СТАТИСТИКА\n\nКак работает: выводит тип (канал/группа), участников, онлайн, админов, средние просмотры на пост (для каналов) и среднее кол-во постов в неделю. Можно выбрать путь сохранения.\n\nПрава: достаточно быть участником. Админ не нужен.",
    },
    "en": {
        "title": "Psylocyba Tools",
        "subtitle": "Clone groups & channels · Export subscribers",
        "api_settings": "API Settings",
        "api_hint": "API ID and Hash — see guide below",
        "api_id": "API ID",
        "api_hash": "API Hash",
        "phone": "Phone",
        "phone_hint": "With + (e.g. +79001234567)",
        "save": "Save",
        "install_deps": "Install Dependencies",
        "auth": "Authorization",
        "help_api": "? How to get API",
        "clone_group": "Clone Group",
        "clone_channel": "Clone Channel",
        "export": "Export Subscribers",
        "link_group": "Link or @username of group:",
        "name_group": "New group name (empty = same as source):",
        "run_clone_group": "Run Clone",
        "link_channel": "Link or @username of channel:",
        "name_channel": "New channel name (empty = same as source):",
        "link_export": "Link or @username of channel/chat:",
        "file_save": "Save to file:",
        "browse": "Browse...",
        "run_export": "Run Export",
        "log": "Log",
        "saved": "Settings saved.",
        "done": "Dependencies installed.",
        "err_install": "Installation failed.",
        "enter_link_group": "Enter group link.",
        "enter_link_channel": "Enter channel link.",
        "enter_link_export": "Enter channel/chat link.",
        "lang": "Language",
        "select_lang": "Select language",
        "close": "Close",
        "auth_success": "Authorization successful!",
        "auth_err": "Authorization failed.",
        "clone_success": "Cloning completed successfully.",
        "clone_err": "Cloning failed.",
        "export_success": "Export completed successfully.",
        "export_err": "Export failed.",
        "stop": "Stop",
        "stop_confirm": "Stopping will interrupt copying/export. Continue?",
        "stop_confirm2": "Really stop?",
        "stopped": "Stopped.",
        "no_scripts": "No scripts running.",
        "stop_no_exe": "Stop is not available in exe mode.",
        "progress_collecting": "Collecting messages: {n}",
        "progress_copying": "Copying: {cur} / {total}",
        "progress_exporting": "Exporting: {n}",
        "license_title": "License",
        "license_enter": "Enter license key:",
        "license_activate": "Activate (or Enter)",
        "license_invalid": "Invalid key.",
        "license_bound": "Key is bound to another computer.",
        "license_network": "Server unavailable. Wait a minute and try again.",
        "mass_send": "Mass Mailing",
        "stats": "Statistics",
        "link_mass": "Channel/group link:",
        "message_text": "Message text:",
        "delay_sec": "Delay between messages (sec):",
        "run_mass_send": "Run Mailing",
        "mass_success": "Mailing completed.",
        "mass_err": "Mailing failed.",
        "link_stats": "Channel/group link:",
        "run_stats": "Get Statistics",
        "stats_success": "Statistics received.",
        "stats_err": "Failed to get statistics.",
        "export_format": "Export format:",
        "export_include_bots": "Include bots",
        "check_log_hint": "Check the log below for details.",
        "help_clone_group": "CLONE GROUP\n\nHow it works: creates a new group, copies avatar, description and all messages (including forum topics).\n\nPermissions: you only need to be a member of the source group. Admin not required.",
        "help_clone_channel": "CLONE CHANNEL\n\nHow it works: creates a new channel, copies avatar, description and all posts with media.\n\nPermissions: you only need to be a subscriber of the source channel. Admin not required.",
        "help_export": "EXPORT SUBSCRIBERS\n\nHow it works: collects the list of channel/group members and saves to file (ID, name, @username in selected format). Bots are excluded by default.\n\nPermissions: admin rights required in the channel or group.",
        "help_mass_send": "MASS MAILING\n\nHow it works: gets the participant list, then sends each person a private message (DM) with the specified delay. Bots and deleted accounts are skipped.\n\nPermissions: admin rights required in the channel or group.",
        "help_stats": "STATISTICS\n\nHow it works: shows type (channel/group), participants, online, admins, average views per post (channels), average posts per week. You can choose save path.\n\nPermissions: you only need to be a member. Admin not required.",
    },
}

API_HELP_RU = """
═══════════════════ КАК ПОЛУЧИТЬ API ID И API HASH ═══════════════════

Шаг 1. Откройте сайт в браузере:
        https://my.telegram.org

Шаг 2. Войдите в свой аккаунт Telegram.
        Введите номер телефона (через +, например +79001234567).
        Вам придёт код — введите его на сайте.

Шаг 3. После входа нажмите «API development tools».

Шаг 4. Заполните форму создания приложения:
        • App title — любое название (например: Psylocyba Tools)
        • Short name — короткое имя (латиницей, например: psytools)
        • Platform — выберите Desktop
        • Description — можно оставить пустым

Шаг 5. Нажмите «Create application».

Шаг 6. На открывшейся странице вы увидите:
        • api_id — число (например: 12345678)
        • api_hash — длинная строка букв и цифр

Шаг 7. Скопируйте оба значения и вставьте в поля выше.

═══════════════════════════════════════════════════════════════════════

Если форма не отправляется или показывает ERROR:
• Попробуйте другой браузер (Chrome, Firefox)
• Отключите VPN или попробуйте с VPN
• Номер телефона — обязательно через + (например +79001234567)
"""

API_HELP_EN = """
═══════════════ HOW TO GET API ID AND API HASH ═══════════════

Step 1. Open in your browser:
        https://my.telegram.org

Step 2. Log in with your Telegram account.
        Enter your phone number (with +, e.g. +79001234567).
        You will receive a code — enter it on the site.

Step 3. After login, click «API development tools».

Step 4. Fill in the application form:
        • App title — any name (e.g. Psylocyba Tools)
        • Short name — short name (Latin, e.g. psytools)
        • Platform — select Desktop
        • Description — can be left empty

Step 5. Click «Create application».

Step 6. On the page that opens you will see:
        • api_id — a number (e.g. 12345678)
        • api_hash — a long string of letters and numbers

Step 7. Copy both values and paste them into the fields above.

═══════════════════════════════════════════════════════════════

If the form doesn't submit or shows ERROR:
• Try a different browser (Chrome, Firefox)
• Disable VPN or try with VPN
• Phone number — must start with + (e.g. +79001234567)
"""


try:
    import customtkinter as ctk
    HAS_CTK = True
except ImportError:
    HAS_CTK = False


def _license_check_enabled():
    # На Mac лицензию не проверяем
    if sys.platform == "darwin":
        return False
    url = (LICENSE_SERVER_URL or "").strip().lower()
    return url and url not in ("", "skip", "0", "false")


def _check_license_sync():
    """Проверка лицензии (синхронно). Возвращает True если ключ валиден или проверка отключена."""
    if not _license_check_enabled():
        return True
    lic = load_license()
    key = lic.get("key", "").strip()
    if not key:
        return False
    hwid = get_hwid()
    valid, err = verify_license(key, hwid)
    if valid:
        return True
    clear_license()
    return False


def _show_license_dialog(attempt=0):
    """Диалог ввода ключа. На Mac — нативный osascript (tk/CTk там глючат с кликами)."""
    if not _license_check_enabled():
        return True
    cfg = load_config()
    lang = cfg.get("lang", "ru")
    t = lambda k: LANG.get(lang, LANG["en"]).get(k, k)

    if sys.platform == "darwin":
        # Нативный диалог macOS — только ASCII для надёжности в .app
        script = (
            'set r to display dialog "Enter license key:" default answer "" '
            'with title "License" buttons {"Activate", "Cancel"} default button 1\n'
            'if button returned of r is "Activate" then return text returned of r else return ""'
        )
        key = ""
        try:
            r = subprocess.run(
                ["/usr/bin/osascript", "-e", script],
                capture_output=True, text=True, timeout=300,
                env=dict(os.environ, PATH="/usr/bin:/bin:/usr/sbin:/sbin"),
            )
            key = (r.stdout or "").strip() if r.returncode == 0 else ""
        except Exception:
            pass
        if not key:
            try:
                import tkinter as tk
                from tkinter import simpledialog
                root = tk.Tk()
                root.withdraw()
                root.attributes("-topmost", True)
                key = simpledialog.askstring("License", "Enter license key:", parent=root) or ""
                root.destroy()
            except Exception:
                pass
        if not key:
            return False
    else:
        # Windows/Linux — tkinter
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.title(t("license_title"))
        root.geometry("420x180")
        root.resizable(False, False)
        root.configure(bg="#1a1a2e")
        result = [None]

        def on_activate():
            key = entry.get().strip()
            if not key:
                messagebox.showwarning("", t("license_enter"))
                return
            hwid = get_hwid()
            valid, err = verify_license(key, hwid)
            if valid:
                save_license(key)
                result[0] = True
                root.destroy()
            else:
                msg = t("license_invalid") if err == "invalid" else (t("license_bound") if err == "key_bound" else t("license_network"))
                messagebox.showerror("", msg)

        tk.Label(root, text=t("license_enter"), fg="#00ffe8", bg="#1a1a2e", font=("Segoe UI", 12)).pack(pady=(20, 8))
        entry = tk.Entry(root, width=40, font=("Segoe UI", 12), relief="flat", bg="#2a2a4e", fg="#fff", insertbackground="#fff")
        entry.pack(pady=(0, 20), ipady=8, ipadx=8)
        entry.bind("<Return>", lambda e: on_activate())
        tk.Button(root, text=t("license_activate"), command=on_activate, width=18, bg="#00ff88", fg="#000",
                 font=("Segoe UI", 11, "bold"), relief="flat", cursor="hand2").pack(pady=(0, 20))
        entry.focus()
        root.mainloop()
        if result[0] is not True:
            return False
        return True

    # Mac path: key получен, проверяем
    hwid = get_hwid()
    valid, err = verify_license(key, hwid)
    if valid:
        save_license(key)
        return True
    msg = t("license_invalid") if err == "invalid" else (t("license_bound") if err == "key_bound" else t("license_network"))
    if sys.platform == "darwin":
        msg_esc = msg.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
        subprocess.run(["/usr/bin/osascript", "-e", f'display alert "License" message "{msg_esc}" as critical'], check=False)
    else:
        from tkinter import messagebox
        messagebox.showerror("", msg)
    # При ошибке сети — дать ещё одну попытку (сервер мог «проснуться»)
    if err == "network" and attempt < 1:
        return _show_license_dialog(attempt + 1)
    return False


def create_app():
    if HAS_CTK:
        return CtkApp()
    return None


class CtkApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        cfg = load_config()
        self.lang = cfg.get("lang", "ru")
        self._t = lambda k: LANG.get(self.lang, LANG["en"]).get(k, k)

        self.title("Psylocyba Tools")
        self.geometry("840x800")
        self.minsize(700, 640)

        self.configure(fg_color="#080510")
        self.cyan = "#00ffe8"
        self.magenta = "#ff0099"
        self.lime = "#00ff88"
        self.purple = "#a855f7"
        self.text = "#e8e8f5"
        self.muted = "#7070a0"
        self.bg_card = "#100816"
        self.bg_input = "#0c0812"
        self.bg_dropdown = "#140a1c"

        self._font_title = ctk.CTkFont(family="Segoe UI", size=30, weight="bold")
        self._font_sub = ctk.CTkFont(family="Segoe UI", size=13)
        self._font_btn = ctk.CTkFont(family="Segoe UI Semibold", size=13)

        self._run_procs = []
        self._build_ui()
        self._fix_ru_keyboard_paste()

    def _start_progress_poll(self, progress_path):
        def poll():
            if self._progress_poll_id is None:
                return
            try:
                p = Path(progress_path)
                if p.exists():
                    s = p.read_text(encoding="utf-8").strip()
                    parts = s.split("|")
                    if len(parts) >= 3:
                        phase, cur, total = parts[0], int(parts[1]), int(parts[2])
                        if total > 0:
                            self.progress_var.set(cur / total)
                            self.progress_label.configure(text=self._t("progress_copying").format(cur=cur, total=total))
                        else:
                            text = self._t("progress_collecting").format(n=cur) if phase == "collect" else self._t("progress_exporting").format(n=cur)
                            self.progress_label.configure(text=text)
            except Exception:
                pass
            if self._progress_poll_id is not None:
                self._progress_poll_id = self.after(500, poll)
        self.progress_var.set(0)
        self.progress_label.configure(text="...")
        self._progress_poll_id = "run"
        self.after(300, poll)

    def _stop_progress_poll(self):
        if self._progress_poll_id and self._progress_poll_id != "run":
            self.after_cancel(self._progress_poll_id)
        self._progress_poll_id = None
        self.progress_var.set(1.0)
        self.progress_label.configure(text="")

    def _do_stop_script(self):
        from tkinter import messagebox
        if not self._run_procs:
            messagebox.showinfo("", self._t("no_scripts"))
            return
        if not messagebox.askyesno("", self._t("stop_confirm")):
            return
        if not messagebox.askyesno("", self._t("stop_confirm2")):
            return
        self._stop_progress_poll()
        for p in list(self._run_procs):
            try:
                p.terminate()
                p.wait(timeout=3)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass
        self._run_procs.clear()
        self.log.insert("end", "\n" + self._t("stopped") + "\n")
        messagebox.showinfo("", self._t("stopped"))

    def _fix_ru_keyboard_paste(self):
        """Исправляет Ctrl+V/C/X при русской раскладке (keycode вместо keysym)."""
        def _on_key(event):
            ctrl = (event.state & 0x4) != 0
            if not ctrl:
                return
            w = self.focus_get()
            if not w:
                return
            if event.keycode == 86 and event.keysym.lower() != "v":
                try:
                    w.event_generate("<<Paste>>")
                except Exception:
                    pass
            elif event.keycode == 67 and event.keysym.lower() != "c":
                try:
                    w.event_generate("<<Copy>>")
                except Exception:
                    pass
            elif event.keycode == 88 and event.keysym.lower() != "x":
                try:
                    w.event_generate("<<Cut>>")
                except Exception:
                    pass
        self.bind_all("<KeyRelease>", _on_key, "+")

    def _build_ui(self):
        t = self._t
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(28, 16))

        title_block = ctk.CTkFrame(header, fg_color="transparent")
        title_block.pack(side="left")
        title_row = ctk.CTkFrame(title_block, fg_color="transparent")
        title_row.pack(anchor="w")
        ctk.CTkLabel(title_row, text=t("title"), font=self._font_title,
                     text_color=self.lime).pack(side="left")

        self.channel_btn = ctk.CTkButton(title_row, text="Channel", width=88, height=34,
                                         corner_radius=8, font=ctk.CTkFont(family="Segoe UI", size=12),
                                         fg_color="transparent", hover_color="#180c24",
                                         border_width=1, border_color=self.cyan,
                                         text_color=self.cyan,
                                         command=lambda: webbrowser.open(TELEGRAM_CHANNEL_URL))
        self.channel_btn.pack(side="left", padx=(18, 0))

        ctk.CTkLabel(title_block, text=t("subtitle"), font=self._font_sub,
                     text_color=self.muted).pack(anchor="w", pady=(6, 0))

        self.lang_btn = ctk.CTkButton(
            header, text=("RU" if self.lang == "ru" else "EN"),
            width=52, height=34, corner_radius=8, font=self._font_btn,
            fg_color=self.bg_card, hover_color="#180c24",
            border_width=1, border_color=self.cyan,
            command=self._show_lang_dialog
        )
        self.lang_btn.pack(side="right")

        settings_card = ctk.CTkFrame(
            self, fg_color=self.bg_card, corner_radius=16,
            border_width=1, border_color=self.cyan
        )
        settings_card.pack(fill="x", padx=28, pady=12)
        settings_inner = ctk.CTkFrame(settings_card, fg_color="transparent")
        settings_inner.pack(fill="x", padx=24, pady=22)

        hdr = ctk.CTkFrame(settings_inner, fg_color="transparent")
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text=t("api_settings"), font=ctk.CTkFont(family="Segoe UI Semibold", size=17),
                     text_color=self.cyan).pack(side="left")
        ctk.CTkButton(hdr, text=t("help_api"), width=150, height=34, corner_radius=12,
                      font=self._font_btn, fg_color=self.magenta, hover_color="#ff5aad",
                      command=self._show_api_help).pack(side="right")
        ctk.CTkLabel(settings_inner, text=t("api_hint"), font=self._font_sub,
                     text_color=self.muted).pack(anchor="w", pady=(4, 0))

        cfg = load_config()
        grid = ctk.CTkFrame(settings_inner, fg_color="transparent")
        grid.pack(fill="x", pady=(14, 0))
        ctk.CTkLabel(grid, text=t("api_id"), width=100, font=self._font_sub,
                     text_color=self.text).grid(row=0, column=0, sticky="w", pady=6, padx=(0, 12))
        self.entry_api_id = ctk.CTkEntry(grid, width=140, height=38, corner_radius=10,
                                         fg_color=self.bg_input, text_color=self.text,
                                         font=ctk.CTkFont(size=13))
        self.entry_api_id.grid(row=0, column=1, sticky="w", pady=6)
        self.entry_api_id.insert(0, cfg.get("api_id", ""))
        ctk.CTkLabel(grid, text=t("api_hash"), width=100, font=self._font_sub,
                     text_color=self.text).grid(row=1, column=0, sticky="w", pady=6, padx=(0, 12))
        self.entry_api_hash = ctk.CTkEntry(grid, width=320, height=38, show="•", corner_radius=10,
                                           fg_color=self.bg_input, text_color=self.text,
                                           font=ctk.CTkFont(size=13))
        self.entry_api_hash.grid(row=1, column=1, sticky="w", pady=6)
        self.entry_api_hash.insert(0, cfg.get("api_hash", ""))
        ctk.CTkLabel(grid, text=t("phone"), width=100, font=self._font_sub,
                     text_color=self.text).grid(row=2, column=0, sticky="w", pady=6, padx=(0, 12))
        phone_frame = ctk.CTkFrame(grid, fg_color="transparent")
        phone_frame.grid(row=2, column=1, sticky="w", pady=6)
        self.entry_phone = ctk.CTkEntry(phone_frame, width=220, height=38, corner_radius=10,
                                        fg_color=self.bg_input, text_color=self.text,
                                        placeholder_text=t("phone_hint"),
                                        font=ctk.CTkFont(size=13))
        self.entry_phone.pack(side="left")
        self.entry_phone.insert(0, cfg.get("phone", ""))
        ctk.CTkLabel(phone_frame, text="  " + t("phone_hint"), font=ctk.CTkFont(size=11),
                     text_color=self.muted).pack(side="left")

        btn_row = ctk.CTkFrame(settings_inner, fg_color="transparent")
        btn_row.pack(fill="x", pady=(18, 0))
        ctk.CTkButton(btn_row, text=t("save"), width=110, height=38, corner_radius=12,
                      font=self._font_btn, fg_color=self.lime, hover_color="#00cc6a",
                      text_color="#000", command=self.save_settings).pack(side="left", padx=(0, 12))
        if not getattr(sys, "frozen", False):
            ctk.CTkButton(btn_row, text=t("install_deps"), width=190, height=38, corner_radius=12,
                          font=self._font_btn, fg_color=self.cyan, hover_color="#00c4e6",
                          text_color="#000", command=self.do_install).pack(side="left", padx=(0, 12))
        ctk.CTkButton(btn_row, text=t("auth"), width=120, height=38, corner_radius=12,
                      font=self._font_btn, fg_color=self.magenta, hover_color="#ff5aad",
                      command=self._on_auth_click).pack(side="left")

        self.tabview = ctk.CTkTabview(
            self, fg_color=self.bg_card, corner_radius=18,
            segmented_button_fg_color=self.bg_dropdown,
            segmented_button_selected_color="#1a2d35",
            segmented_button_unselected_color=self.bg_input,
            segmented_button_unselected_hover_color="#1a1a2e",
            text_color="#00ffea"
        )
        self.tabview.pack(fill="both", expand=True, padx=28, pady=10)
        tab_group = self.tabview.add(t("clone_group"))
        tab_channel = self.tabview.add(t("clone_channel"))
        tab_export = self.tabview.add(t("export"))
        tab_mass = self.tabview.add(t("mass_send"))
        tab_stats = self.tabview.add(t("stats"))

        for tab in (tab_group, tab_channel, tab_export, tab_mass, tab_stats):
            tab.configure(fg_color=self.bg_card)

        def mk_entry(parent, w=440):
            return ctk.CTkEntry(parent, width=w, height=40, corner_radius=10,
                                fg_color=self.bg_input, text_color=self.text, font=ctk.CTkFont(size=13))

        grp_label_row = ctk.CTkFrame(tab_group, fg_color="transparent")
        grp_label_row.pack(anchor="w")
        ctk.CTkLabel(grp_label_row, text=t("link_group"), font=self._font_sub, text_color=self.text).pack(side="left")
        self._mk_help_btn(grp_label_row, "help_clone_group").pack(side="left", padx=(8, 0))
        self.entry_group_source = mk_entry(tab_group)
        self.entry_group_source.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(tab_group, text=t("name_group"), font=self._font_sub, text_color=self.text).pack(anchor="w")
        self.entry_group_title = mk_entry(tab_group)
        self.entry_group_title.pack(fill="x", pady=(0, 18))
        grp_btn_row = ctk.CTkFrame(tab_group, fg_color="transparent")
        grp_btn_row.pack(anchor="w")
        ctk.CTkButton(grp_btn_row, text=t("run_clone_group"), width=220, height=40, corner_radius=14,
                      font=self._font_btn, fg_color=self.lime, hover_color="#00cc6a", text_color="#000",
                      command=self.run_clone_group).pack(side="left", padx=(0, 10))
        ctk.CTkButton(grp_btn_row, text=t("stop"), width=100, height=40, corner_radius=14,
                      font=self._font_btn, fg_color="#cc3333", hover_color="#ff4444", text_color="#fff",
                      command=self._do_stop_script).pack(side="left")

        ch_label_row = ctk.CTkFrame(tab_channel, fg_color="transparent")
        ch_label_row.pack(anchor="w")
        ctk.CTkLabel(ch_label_row, text=t("link_channel"), font=self._font_sub, text_color=self.text).pack(side="left")
        self._mk_help_btn(ch_label_row, "help_clone_channel").pack(side="left", padx=(8, 0))
        self.entry_channel_source = mk_entry(tab_channel)
        self.entry_channel_source.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(tab_channel, text=t("name_channel"), font=self._font_sub, text_color=self.text).pack(anchor="w")
        self.entry_channel_title = mk_entry(tab_channel)
        self.entry_channel_title.pack(fill="x", pady=(0, 18))
        ch_btn_row = ctk.CTkFrame(tab_channel, fg_color="transparent")
        ch_btn_row.pack(anchor="w")
        ctk.CTkButton(ch_btn_row, text=t("run_clone_group"), width=220, height=40, corner_radius=14,
                      font=self._font_btn, fg_color=self.lime, hover_color="#00cc6a", text_color="#000",
                      command=self.run_clone_channel).pack(side="left", padx=(0, 10))
        ctk.CTkButton(ch_btn_row, text=t("stop"), width=100, height=40, corner_radius=14,
                      font=self._font_btn, fg_color="#cc3333", hover_color="#ff4444", text_color="#fff",
                      command=self._do_stop_script).pack(side="left")

        exp_label_row = ctk.CTkFrame(tab_export, fg_color="transparent")
        exp_label_row.pack(anchor="w")
        ctk.CTkLabel(exp_label_row, text=t("link_export"), font=self._font_sub, text_color=self.text).pack(side="left")
        self._mk_help_btn(exp_label_row, "help_export").pack(side="left", padx=(8, 0))
        self.entry_export_source = mk_entry(tab_export)
        self.entry_export_source.pack(fill="x", pady=(0, 10))
        exp_opts = ctk.CTkFrame(tab_export, fg_color="transparent")
        exp_opts.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(exp_opts, text=t("export_format"), font=self._font_sub, text_color=self.text).pack(side="left", padx=(0, 8))
        self.export_format_var = ctk.StringVar(value="simple")
        self.export_format_menu = ctk.CTkOptionMenu(exp_opts, variable=self.export_format_var, width=140,
            values=["simple", "csv", "username"], fg_color=self.bg_input)
        self.export_format_menu.pack(side="left", padx=(0, 20))
        self.export_include_bots_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(exp_opts, text=t("export_include_bots"), variable=self.export_include_bots_var,
            font=self._font_sub, text_color=self.text, fg_color=self.cyan).pack(side="left")
        out_row = ctk.CTkFrame(tab_export, fg_color="transparent")
        out_row.pack(fill="x", pady=(0, 18))
        ctk.CTkLabel(out_row, text=t("file_save"), font=self._font_sub, text_color=self.text).pack(side="left", padx=(0, 12))
        self.entry_export_output = mk_entry(out_row, 280)
        self.entry_export_output.pack(side="left", padx=(0, 12))
        self.entry_export_output.insert(0, str(USER_DATA_DIR / "members.txt"))
        ctk.CTkButton(out_row, text=t("browse"), width=100, height=40, corner_radius=10,
                      font=self._font_btn, fg_color=self.cyan, hover_color="#00c4e6", text_color="#000",
                      command=self.browse_output).pack(side="left")
        exp_btn_row = ctk.CTkFrame(tab_export, fg_color="transparent")
        exp_btn_row.pack(anchor="w")
        ctk.CTkButton(exp_btn_row, text=t("run_export"), width=220, height=40, corner_radius=14,
                      font=self._font_btn, fg_color=self.lime, hover_color="#00cc6a", text_color="#000",
                      command=self.run_export).pack(side="left", padx=(0, 10))
        ctk.CTkButton(exp_btn_row, text=t("stop"), width=100, height=40, corner_radius=14,
                      font=self._font_btn, fg_color="#cc3333", hover_color="#ff4444", text_color="#fff",
                      command=self._do_stop_script).pack(side="left")

        mass_label_row = ctk.CTkFrame(tab_mass, fg_color="transparent")
        mass_label_row.pack(anchor="w")
        ctk.CTkLabel(mass_label_row, text=t("link_mass"), font=self._font_sub, text_color=self.text).pack(side="left")
        self._mk_help_btn(mass_label_row, "help_mass_send").pack(side="left", padx=(8, 0))
        self.entry_mass_source = mk_entry(tab_mass)
        self.entry_mass_source.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(tab_mass, text=t("message_text"), font=self._font_sub, text_color=self.text).pack(anchor="w")
        self.entry_mass_message = ctk.CTkTextbox(tab_mass, height=80, font=ctk.CTkFont(size=13),
            fg_color=self.bg_input, text_color=self.text)
        self.entry_mass_message.pack(fill="x", pady=(0, 10))
        mass_delay_row = ctk.CTkFrame(tab_mass, fg_color="transparent")
        mass_delay_row.pack(fill="x", pady=(0, 18))
        ctk.CTkLabel(mass_delay_row, text=t("delay_sec"), font=self._font_sub, text_color=self.text).pack(side="left", padx=(0, 8))
        self.entry_mass_delay = mk_entry(mass_delay_row, 80)
        self.entry_mass_delay.pack(side="left")
        self.entry_mass_delay.insert(0, "2")
        mass_btn_row = ctk.CTkFrame(tab_mass, fg_color="transparent")
        mass_btn_row.pack(anchor="w")
        ctk.CTkButton(mass_btn_row, text=t("run_mass_send"), width=220, height=40, corner_radius=14,
                      font=self._font_btn, fg_color=self.lime, hover_color="#00cc6a", text_color="#000",
                      command=self.run_mass_send).pack(side="left", padx=(0, 10))
        ctk.CTkButton(mass_btn_row, text=t("stop"), width=100, height=40, corner_radius=14,
                      font=self._font_btn, fg_color="#cc3333", hover_color="#ff4444", text_color="#fff",
                      command=self._do_stop_script).pack(side="left")

        stats_label_row = ctk.CTkFrame(tab_stats, fg_color="transparent")
        stats_label_row.pack(anchor="w")
        ctk.CTkLabel(stats_label_row, text=t("link_stats"), font=self._font_sub, text_color=self.text).pack(side="left")
        self._mk_help_btn(stats_label_row, "help_stats").pack(side="left", padx=(8, 0))
        self.entry_stats_source = mk_entry(tab_stats)
        self.entry_stats_source.pack(fill="x", pady=(0, 10))
        stats_out_row = ctk.CTkFrame(tab_stats, fg_color="transparent")
        stats_out_row.pack(fill="x", pady=(0, 18))
        ctk.CTkLabel(stats_out_row, text=t("file_save"), font=self._font_sub, text_color=self.text).pack(side="left", padx=(0, 12))
        self.entry_stats_output = mk_entry(stats_out_row, 280)
        self.entry_stats_output.pack(side="left", padx=(0, 12))
        self.entry_stats_output.insert(0, str(APP_DIR / "stats.txt"))
        ctk.CTkButton(stats_out_row, text=t("browse"), width=100, height=40, corner_radius=10,
                      font=self._font_btn, fg_color=self.cyan, hover_color="#00c4e6", text_color="#000",
                      command=self.browse_stats_output).pack(side="left")
        stats_btn_row = ctk.CTkFrame(tab_stats, fg_color="transparent")
        stats_btn_row.pack(anchor="w")
        ctk.CTkButton(stats_btn_row, text=t("run_stats"), width=220, height=40, corner_radius=14,
                      font=self._font_btn, fg_color=self.lime, hover_color="#00cc6a", text_color="#000",
                      command=self.run_stats).pack(side="left", padx=(0, 10))
        ctk.CTkButton(stats_btn_row, text=t("stop"), width=100, height=40, corner_radius=14,
                      font=self._font_btn, fg_color="#cc3333", hover_color="#ff4444", text_color="#fff",
                      command=self._do_stop_script).pack(side="left")

        log_frame = ctk.CTkFrame(
            self, fg_color=self.bg_card, corner_radius=18,
            border_width=1, border_color=self.magenta
        )
        log_frame.pack(fill="both", expand=True, padx=28, pady=(0, 28))
        log_inner = ctk.CTkFrame(log_frame, fg_color="transparent")
        log_inner.pack(fill="both", expand=True, padx=18, pady=18)
        ctk.CTkLabel(log_inner, text=t("log"), font=ctk.CTkFont(family="Segoe UI Semibold", size=15),
                     text_color=self.magenta).pack(anchor="w")
        prog_frame = ctk.CTkFrame(log_inner, fg_color="transparent")
        prog_frame.pack(fill="x", pady=(10, 6))
        self.progress_var = ctk.DoubleVar(value=0)
        self.progress_bar = ctk.CTkProgressBar(prog_frame, variable=self.progress_var, height=14,
                                               progress_color=self.lime, fg_color=self.bg_input)
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.progress_label = ctk.CTkLabel(prog_frame, text="", font=ctk.CTkFont(size=12, weight="bold"),
                                           text_color=self.cyan, width=120, anchor="e")
        self.progress_label.pack(side="right")
        self._progress_poll_id = None
        self.log = ctk.CTkTextbox(log_inner, height=100,
                                  font=ctk.CTkFont(family="Consolas", size=12),
                                  fg_color=self.bg_input, text_color=self.lime)
        self.log.pack(fill="both", expand=True, pady=(10, 0))

    def _show_lang_dialog(self):
        self.update_idletasks()
        bx = self.lang_btn.winfo_rootx()
        by = self.lang_btn.winfo_rooty() + self.lang_btn.winfo_height() + 4
        pop_w, pop_h = 220, 130

        top = ctk.CTkToplevel(self)
        top.title("")
        top.geometry(f"{pop_w}x{pop_h}")
        top.configure(fg_color=self.bg_dropdown)
        top.resizable(False, False)
        top.transient(self)
        top.grab_set()
        x = bx + self.lang_btn.winfo_width() - pop_w
        if x < 10:
            x = bx
        top.geometry(f"+{x}+{by}")

        frame = ctk.CTkFrame(top, fg_color=self.bg_dropdown, corner_radius=12,
                             border_width=1, border_color=self.cyan)
        frame.pack(fill="both", expand=True, padx=8, pady=8)

        def pick(l):
            cfg = load_config()
            self.lang = l
            cfg["lang"] = l
            save_config(cfg)
            top.destroy()
            for w in self.winfo_children():
                w.destroy()
            self._build_ui()

        opts = [("ru", "Русский"), ("en", "English")]
        for code, name in opts:
            is_sel = self.lang == code
            txt = f"  {name}" + ("  ✓" if is_sel else "")
            btn = ctk.CTkButton(frame, text=txt, height=40, corner_radius=10,
                                anchor="w", font=ctk.CTkFont(size=14),
                                fg_color=self.bg_card if is_sel else "transparent",
                                hover_color="#1a1530", text_color=self.lime if is_sel else self.text,
                                command=lambda c=code: pick(c))
            btn.pack(fill="x", pady=3)

        top.after(30, lambda: animate_fade_in(top))

    def _show_api_help(self):
        top = ctk.CTkToplevel(self)
        top.title("API ID & Hash — " + ("Инструкция" if self.lang == "ru" else "Guide"))
        top.geometry("580x560")
        top.configure(fg_color=self.bg_card)
        top.transient(self)
        txt = API_HELP_RU if self.lang == "ru" else API_HELP_EN
        frame = ctk.CTkFrame(top, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=24, pady=24)
        tb = ctk.CTkTextbox(frame, font=ctk.CTkFont(family="Segoe UI", size=12),
                            fg_color=self.bg_input, text_color=self.cyan, wrap="word")
        tb.pack(fill="both", expand=True)
        tb.insert("1.0", txt)
        tb.configure(state="disabled")
        ctk.CTkButton(frame, text=self._t("close"), width=110, height=38, corner_radius=12,
                      font=self._font_btn, fg_color=self.magenta, hover_color="#ff5aad",
                      command=top.destroy).pack(pady=(14, 0))
        top.after(50, lambda: animate_fade_in(top))

    def _mk_help_btn(self, parent, help_key):
        return ctk.CTkButton(parent, text="?", width=28, height=28, corner_radius=14,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.cyan, hover_color="#00c4e6", text_color="#000",
            command=lambda k=help_key: self._show_feature_help(k))

    def _show_feature_help(self, key):
        top = ctk.CTkToplevel(self)
        top.title("?" if self.lang == "ru" else "Help")
        top.geometry("480x320")
        top.configure(fg_color=self.bg_card)
        top.transient(self)
        frame = ctk.CTkFrame(top, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=24, pady=24)
        tb = ctk.CTkTextbox(frame, font=ctk.CTkFont(family="Segoe UI", size=12),
                            fg_color=self.bg_input, text_color=self.cyan, wrap="word")
        tb.pack(fill="both", expand=True)
        tb.insert("1.0", self._t(key))
        tb.configure(state="disabled")
        ctk.CTkButton(frame, text=self._t("close"), width=110, height=38, corner_radius=12,
                      font=self._font_btn, fg_color=self.magenta, hover_color="#ff5aad",
                      command=top.destroy).pack(pady=(14, 0))
        top.after(50, lambda: animate_fade_in(top))

    def _on_auth_click(self):
        """Нажатие «Авторизация»: сначала сохраняем настройки; на Mac save может падать — тогда всё равно запускаем авторизацию."""
        try:
            self.save_settings(silent=True)
        except Exception:
            pass
        run_auth(self, self.log)

    def save_settings(self, silent=False):
        cfg = load_config()
        cfg["api_id"] = self.entry_api_id.get().strip()
        cfg["api_hash"] = self.entry_api_hash.get().strip()
        cfg["phone"] = self.entry_phone.get().strip()
        cfg["lang"] = self.lang
        save_config(cfg)
        if not silent:
            if sys.platform == "darwin":
                _show_message_inline(self, self._t("saved"), is_error=False)
            else:
                from tkinter import messagebox
                messagebox.showinfo("", self._t("saved"))

    def do_install(self):
        self.log.delete("1.0", "end")
        self.log.insert("end", "Installing...\n")
        def install():
            ok = install_deps()
            self.after(0, lambda: self._install_done(ok))
        threading.Thread(target=install, daemon=True).start()

    def _install_done(self, ok):
        from tkinter import messagebox
        if ok:
            self.log.insert("end", "Done.\n")
            messagebox.showinfo("", self._t("done"))
        else:
            self.log.insert("end", "Error.\n")
            messagebox.showerror("", self._t("err_install"))

    def browse_output(self):
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("*.txt", "*.txt")],
            initialdir=str(APP_DIR),
        )
        if path:
            self.entry_export_output.delete(0, "end")
            self.entry_export_output.insert(0, path)

    def browse_stats_output(self):
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("*.txt", "*.txt")],
            initialdir=str(APP_DIR),
        )
        if path:
            self.entry_stats_output.delete(0, "end")
            self.entry_stats_output.insert(0, path)

    def run_clone_group(self):
        from tkinter import messagebox
        self.save_settings()
        source = self.entry_group_source.get().strip()
        if not source:
            messagebox.showwarning("", self._t("enter_link_group"))
            return
        pp = str(APP_DIR / ".progress_clone")
        self._start_progress_poll(pp)
        run_script("telegram_clone_group.py", ["--source", source, "--title", self.entry_group_title.get().strip()],
                   self.log, self, proc_holder=self._run_procs,
                   on_done=lambda: messagebox.showinfo("", self._t("clone_success")),
                   on_error=lambda e: messagebox.showerror("", f"{self._t('clone_err')} {e}"),
                   progress_path=pp, on_finish=self._stop_progress_poll)

    def run_clone_channel(self):
        from tkinter import messagebox
        self.save_settings()
        source = self.entry_channel_source.get().strip()
        if not source:
            messagebox.showwarning("", self._t("enter_link_channel"))
            return
        pp = str(APP_DIR / ".progress_clone")
        self._start_progress_poll(pp)
        run_script("telegram_clone_channel.py", ["--source", source, "--title", self.entry_channel_title.get().strip()],
                   self.log, self, proc_holder=self._run_procs,
                   on_done=lambda: messagebox.showinfo("", self._t("clone_success")),
                   on_error=lambda e: messagebox.showerror("", f"{self._t('clone_err')} {e}"),
                   progress_path=pp, on_finish=self._stop_progress_poll)

    def run_export(self):
        from tkinter import messagebox
        self.save_settings()
        source = self.entry_export_source.get().strip()
        if not source:
            messagebox.showwarning("", self._t("enter_link_export"))
            return
        output = self.entry_export_output.get().strip() or "members.txt"
        fmt = self.export_format_var.get()
        incl_bots = "--include-bots" if self.export_include_bots_var.get() else ""
        args = ["--source", source, "--output", output, "--format", fmt]
        if incl_bots:
            args.append(incl_bots)
        pp = str(APP_DIR / ".progress_export")
        self._start_progress_poll(pp)
        run_script("telegram_export_members.py", args,
                   self.log, self, proc_holder=self._run_procs,
                   on_done=lambda: messagebox.showinfo("", self._t("export_success")),
                   on_error=lambda e: messagebox.showerror("", f"{self._t('export_err')} {e}"),
                   progress_path=pp, on_finish=self._stop_progress_poll)

    def run_mass_send(self):
        from tkinter import messagebox
        self.save_settings()
        source = self.entry_mass_source.get().strip()
        if not source:
            messagebox.showwarning("", self._t("enter_link_export"))
            return
        msg = self.entry_mass_message.get("1.0", "end").strip()
        if not msg:
            messagebox.showwarning("", self._t("message_text"))
            return
        try:
            delay = float(self.entry_mass_delay.get().strip() or "2")
        except ValueError:
            delay = 2.0
        msg_file = APP_DIR / ".mass_msg_temp"
        msg_file.write_text(msg, encoding="utf-8")
        pp = str(APP_DIR / ".progress_clone")
        self._start_progress_poll(pp)
        run_script("telegram_mass_send.py", ["--source", source, "--message-file", str(msg_file), "--delay", str(delay)],
                   self.log, self, proc_holder=self._run_procs,
                   on_done=lambda: messagebox.showinfo("", self._t("mass_success")),
                   on_error=lambda e: messagebox.showerror("", f"{self._t('mass_err')} {e}"),
                   progress_path=pp, on_finish=self._stop_progress_poll)

    def run_stats(self):
        from tkinter import messagebox
        self.save_settings()
        source = self.entry_stats_source.get().strip()
        if not source:
            messagebox.showwarning("", self._t("enter_link_export"))
            return
        out_file = self.entry_stats_output.get().strip() or str(APP_DIR / "stats.txt")
        run_script("telegram_stats.py", ["--source", source, "--output", out_file],
                   self.log, self, proc_holder=self._run_procs,
                   on_done=lambda: messagebox.showinfo("", self._t("stats_success")),
                   on_error=lambda e: messagebox.showerror("", f"{self._t('stats_err')} {e}\n\n{self._t('check_log_hint')}"))


def _run_script_mode():
    """Режим --script: запуск скрипта из exe для возможности Stop."""
    argv = sys.argv[1:]
    if len(argv) < 2 or argv[0] != "--script":
        return False

    if not _check_license_sync():
        print("Error: Valid license required. Run the main application to activate.", file=sys.stderr)
        sys.exit(1)

    name = argv[1]
    args = argv[2:]
    os.environ["TELEGRAM_APP_DIR"] = str(USER_DATA_DIR)
    scripts_path = Path(sys._MEIPASS) / "scripts" if getattr(sys, "frozen", False) else SCRIPTS_DIR
    sys.path.insert(0, str(scripts_path))
    try:
        if name == "telegram_clone_group.py":
            from telegram_clone_group import main as m
            src = args[args.index("--source") + 1] if "--source" in args else ""
            tit = args[args.index("--title") + 1] if "--title" in args else ""
            asyncio.run(m(src, tit))
        elif name == "telegram_clone_channel.py":
            from telegram_clone_channel import main as m
            src = args[args.index("--source") + 1] if "--source" in args else ""
            tit = args[args.index("--title") + 1] if "--title" in args else ""
            asyncio.run(m(src, tit))
        elif name == "telegram_export_members.py":
            from telegram_export_members import run_export
            def get_arg(key, default=""):
                try:
                    idx = args.index(key)
                    if idx + 1 < len(args):
                        return args[idx + 1]
                except (ValueError, IndexError):
                    pass
                return default
            src = get_arg("--source", "")
            if not src:
                raise ValueError("--source argument is required")
            out = get_arg("--output", "members.txt")
            fmt = get_arg("--format", "simple")
            incl = "--include-bots" in args
            asyncio.run(run_export(src, out, fmt, incl))
        elif name == "telegram_mass_send.py":
            from telegram_mass_send import run_mass_send
            src = args[args.index("--source") + 1] if "--source" in args else ""
            msg = ""
            if "--message-file" in args:
                mf = args[args.index("--message-file") + 1]
                if Path(mf).exists():
                    msg = Path(mf).read_text(encoding="utf-8")
            else:
                msg = args[args.index("--message") + 1] if "--message" in args else ""
            dly = float(args[args.index("--delay") + 1]) if "--delay" in args else 2.0
            asyncio.run(run_mass_send(src, msg, dly))
        elif name == "telegram_stats.py":
            from telegram_stats import run_stats
            src = args[args.index("--source") + 1] if "--source" in args else ""
            out = args[args.index("--output") + 1] if "--output" in args else ""
            asyncio.run(run_stats(src, out))
        else:
            print(f"Unknown script: {name}")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    return True


if __name__ == "__main__":
    if getattr(sys, "frozen", False) and _run_script_mode():
        sys.exit(0)

    if not _check_license_sync():
        if HAS_CTK and _show_license_dialog():
            pass
        else:
            sys.exit(1)

    if not _check_license_sync():
        sys.exit(1)

    app = create_app()
    if app:
        app.mainloop()
