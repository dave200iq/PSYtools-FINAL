# Render — подробная инструкция

Пошагово, что именно нажимать и куда вводить.

---

## ШАГ 0: Подготовка

У тебя уже должен быть репозиторий на GitHub с файлами:
- `license_server/server_render.py`
- `license_server/requirements-render.txt`

Если нет — сначала создай репо и загрузи эти файлы.

---

## ШАГ 1: Регистрация на Render

1. Открой браузер, зайди на **https://render.com**
2. Нажми **Get Started** (или **Sign In**)
3. Выбери **Sign in with GitHub**
4. Разреши доступ (Authorize)
5. Попадёшь в Dashboard (панель управления)

---

## ШАГ 2: Создание базы данных PostgreSQL

1. В правом верхнем углу нажми синюю кнопку **New +**
2. В меню выбери **PostgreSQL**
3. Откроется форма. Заполни:
   - **Name:** `psylocyba-db` (можно другое, но запомни)
   - **Database:** оставь как есть
   - **User:** создастся автоматически
   - **Region:** выбери **Frankfurt (EU Central)** или ближайший
   - **PostgreSQL Version:** последняя (по умолчанию)
   - **Plan:** выбери **Free**
4. Прокрути вниз, нажми **Create Database**
5. Подожди 1–2 минуты. Статус станет зелёным: **Available**
6. Кликни по созданной базе `psylocyba-db`
7. Вкладка **Info** или **Connect** — найди блок **Connections**
8. Скопируй **Internal Database URL** (именно Internal, не External)
   - Похож на: `postgres://user:password@host/database`
   - Сохрани его в блокнот — понадобится дальше

---

## ШАГ 3: Создание Web Service (веб-сервиса)

1. Вернись в Dashboard (логотип Render вверху слева или кнопка Back)
2. Снова нажми **New +**
3. Выбери **Web Service**
4. Откроется экран **Create a new Web Service**
5. Если GitHub ещё не подключён:
   - Нажми **Connect account** или **Configure account**
   - Выбери **GitHub** и разреши доступ
   - Выбери репозиторий, к которому дать доступ (можно All repositories или только нужный)
6. В списке репозиториев найди свой (например, `psylocyba-license`)
7. Нажми **Connect** рядом с ним
8. Откроется форма настроек сервиса

---

## ШАГ 4: Настройка Web Service

Заполняй по порядку:

### Basic

- **Name:** `psylocyba-license` (это будет часть твоего URL)
- **Region:** тот же, что у базы (Frankfurt)
- **Branch:** `main` (или `master` — как в твоём репо)

### Build & Deploy

- **Root Directory:** впиши `license_server`
  - Это важно: Render будет искать файлы в этой папке
- **Runtime:** **Python 3**
- **Build Command:** впиши:
  ```
  pip install -r requirements-render.txt
  ```
- **Start Command:** впиши:
  ```
  gunicorn server_render:app
  ```

### Instance Type

- Оставь **Free** (если доступно)

---

## ШАГ 5: Переменные окружения (Environment)

1. Прокрути до блока **Environment Variables** (или **Environment**)
2. Нажми **Add Environment Variable** или **+ Add**
3. В поле **Key** впиши: `DATABASE_URL`
4. В поле **Value** вставь **Internal Database URL** из шага 2
   - Никаких пробелов в начале и конце
   - Скопируй полностью, от `postgres://` до конца
5. Нажми **Add** или галочку

---

## ШАГ 6: Создание и деплой

1. Прокрути вниз
2. Нажми **Create Web Service** (синяя кнопка)
3. Начнётся деплой. Подожди 2–5 минут
4. Смотри логи — сначала Build, потом Deploy
5. Когда статус станет **Live** (зелёный) — готово

---

## ШАГ 7: Твой URL

1. Вверху страницы сервиса будет **URL**
2. Формат: `https://psylocyba-license.onrender.com`
3. Скопируй его

Проверка: открой этот URL в браузере. Должно появиться что-то вроде:
```json
{"status":"ok","service":"Psylocyba License Server"}
```

---

## ШАГ 8: Обновление приложения

1. Открой проект Psylocyba_Tools
2. Файл `app.py`
3. Найди строку `LICENSE_SERVER_URL = ...`
4. Замени на:
   ```python
   LICENSE_SERVER_URL = "https://psylocyba-license.onrender.com"
   ```
   (подставь свой URL)
5. Сохрани
6. Запусти `build_exe.bat`
7. Новый exe будет в папке `dist\`

---

## ШАГ 9: Добавление ключей

Открой командную строку в папке `license_server`:

Один ключ:
```
python add_key_remote.py https://psylocyba-license.onrender.com XXXX-XXXX-XXXX-XXXX
```

Несколько ключей (например, 10):
```
python generate_keys_remote.py https://psylocyba-license.onrender.com 10
```

---

## Важно

- **Free tier:** после 15 минут без запросов сервис «засыпает». Первый запрос после этого может идти 30–60 секунд — это нормально.
- Если что-то падает — смотри **Logs** в Render (вкладка Logs у твоего Web Service).

---

## Если что-то пошло не так

**Ошибка при Build:**
- Проверь, что Root Directory = `license_server`
- Проверь, что в репо есть `license_server/requirements-render.txt` и `license_server/server_render.py`

**Ошибка при старте (Start):**
- Проверь переменную `DATABASE_URL` — она должна быть Internal URL от PostgreSQL
- Проверь, что база создана и в статусе Available

**Сайт не открывается:**
- Подожди ещё пару минут
- Проверь, что деплой завершился (статус Live)
