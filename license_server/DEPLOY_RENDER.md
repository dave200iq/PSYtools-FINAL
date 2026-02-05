# Развёртывание на Render

Render работает без VPN в России. Бесплатный тариф.

## Шаг 1: Регистрация

1. Зайди на [render.com](https://render.com)
2. Нажми **Get Started** → войди через **GitHub** (или email)
3. Подтверди email если нужно

## Шаг 2: Создание базы данных

1. В панели Render нажми **New +** → **PostgreSQL**
2. **Name:** `psylocyba-db`
3. **Plan:** Free
4. **Region:** Frankfurt или любой
5. Нажми **Create Database**
6. Дождись создания. Скопируй **Internal Database URL** (Internal) — он нужен для связи сервисов внутри Render

## Шаг 3: Создание Web Service

1. **New +** → **Web Service**
2. Подключи репозиторий GitHub (создай репозиторий с папкой `license_server` если ещё нет)
3. Или выбери **Build and deploy from a GitHub repository** и укажи репозиторий
4. Настройки:
   - **Name:** `psylocyba-license`
   - **Region:** Frankfurt
   - **Branch:** main
   - **Root Directory:** `license_server` (если license_server в корне репо — укажи путь)
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements-render.txt`
   - **Start Command:** `gunicorn server_render:app`
5. **Environment:**
   - Добавь переменную: **Key** `DATABASE_URL`, **Value** — вставь **Internal Database URL** из шага 2
6. **Create Web Service**

## Шаг 4: Деплой без GitHub (если нет репо)

Если нет GitHub-репозитория:

1. Создай папку `license_server_render`
2. Положи туда: `server_render.py`, `requirements-render.txt`
3. Залей на GitHub или используй **Manual Deploy** (Render позволяет загрузить ZIP)
4. Для Manual Deploy: создай Web Service, в Settings → Build & Deploy выбери "Docker" или загрузи через CLI

**Проще всего:** создай репозиторий на GitHub, залей туда папку `license_server` (с server_render.py, requirements-render.txt), подключи к Render.

## Шаг 5: Получи URL

После деплоя Render даст URL, например:
`https://psylocyba-license.onrender.com`

## Шаг 6: Обнови приложение

В `app.py`:
```python
LICENSE_SERVER_URL = "https://ТВОЙ-СЕРВИС.onrender.com"
```

Пересобери exe.

## Шаг 7: Добавь ключи

```
python add_key_remote.py https://ТВОЙ-СЕРВИС.onrender.com XXXX-XXXX-XXXX-XXXX
```

Или:
```
python generate_keys_remote.py https://ТВОЙ-СЕРВИС.onrender.com 10
```

## Важно

- **Free tier:** сервис «засыпает» после 15 мин без активности. Первый запрос после паузы может занять 30–60 сек — это нормально.
- **База данных:** ключи хранятся в PostgreSQL, не теряются при перезапуске.
