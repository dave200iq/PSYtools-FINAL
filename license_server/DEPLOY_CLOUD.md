# Развёртывание сервера в облаке (без роутера)

Сервер будет работать в интернете. Проброс портов не нужен.

## PythonAnywhere (бесплатно)

### 1. Регистрация
- Зайди на [pythonanywhere.com](https://www.pythonanywhere.com)
- Нажми **Pricing & signup** → **Create a Beginner account** (бесплатно)

### 2. Создание веб-приложения
- Вкладка **Web** → **Add a new web app** → **Next**
- Выбери **Flask** → **Next** → **Python 3.10** → **Next**
- Папка приложения появится, например: `/home/ТВОЙ_ЛОГИН/mysite/`

### 3. Загрузка файлов
- Вкладка **Files** → открой папку `mysite` (или как она названа)
- Удали файл `flask_app.py` (или переименуй)
- Нажми **Upload a file** → загрузи `server.py` из папки `license_server`
- Создай файл `keys.json` с содержимым: `{}`

### 4. Настройка WSGI
- Вкладка **Web** → найди **Code** → **WSGI configuration file**
- Нажми на ссылку (например `/var/www/твойлогин_pythonanywhere_com_wsgi.py`)
- Замени всё содержимое на:

```python
import sys
path = '/home/ТВОЙ_ЛОГИН/mysite'
if path not in sys.path:
    sys.path.append(path)
from server import app as application
```

Замени `ТВОЙ_ЛОГИН` на свой логин и `mysite` на имя твоей папки.

### 5. Перезапуск
- Вкладка **Web** → нажми **Reload** (зелёная кнопка)

### 6. Адрес сервера
Твой сервер: `https://ТВОЙ_ЛОГИН.pythonanywhere.com`

### 7. Настрой приложение
В `app.py` перед сборкой exe:
```python
LICENSE_SERVER_URL = "https://ТВОЙ_ЛОГИН.pythonanywhere.com"
```

### 8. Добавление ключей
Через браузер или curl:
```
https://ТВОЙ_ЛОГИН.pythonanywhere.com/add
```
Метод POST, параметр `key=XXXX-XXXX-XXXX-XXXX`

Или используй скрипт `add_key_remote.py` (см. ниже).
