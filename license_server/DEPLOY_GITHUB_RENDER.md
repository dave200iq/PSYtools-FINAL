# Развёртывание на Render через GitHub

Пошаговая инструкция.

---

## Часть 1: GitHub

### 1. Создай аккаунт или войди
[github.com](https://github.com) → Sign up / Log in

### 2. Создай репозиторий
- **New repository**
- **Repository name:** `psylocyba-license` (или любое)
- **Public**
- **Create repository**

### 3. Залей файлы

Нужно загрузить в репозиторий:

**Вариант А — через веб-интерфейс:**

1. В репо нажми **Add file** → **Create new file**
2. Имя файла: `license_server/server_render.py`
3. Скопируй содержимое из `server_render.py` и вставь
4. **Commit new file**
5. **Add file** → **Create new file**
6. Имя: `license_server/requirements-render.txt`
7. Содержимое:
```
flask>=2.0
gunicorn
psycopg2-binary
```
8. **Commit new file**

**Вариант Б — через Git (если установлен):**
```bash
cd "C:\Users\dave2\OneDrive\Рабочий стол\Psylocyba_Tools"
git init
git add license_server/server_render.py license_server/requirements-render.txt
git commit -m "License server"
git branch -M main
git remote add origin https://github.com/ТВОЙ_ЛОГИН/psylocyba-license.git
git push -u origin main
```

---

## Часть 2: Render

### 4. Регистрация
[render.com](https://render.com) → **Get Started** → **Sign in with GitHub**

Разреши Render доступ к GitHub.

### 5. База данных
- **New +** → **PostgreSQL**
- **Name:** `psylocyba-db`
- **Plan:** Free
- **Create Database**
- Дождись зелёного статуса
- Открой базу → **Info** → скопируй **Internal Database URL**

### 6. Web Service
- **New +** → **Web Service**
- Подключи репозиторий `psylocyba-license` (или как назвал)
- Если не видно — **Configure account** и выдай доступ к нужному репо

**Настройки:**
- **Name:** `psylocyba-license`
- **Region:** Frankfurt
- **Branch:** main
- **Root Directory:** `license_server`
- **Runtime:** Python 3
- **Build Command:** `pip install -r requirements-render.txt`
- **Start Command:** `gunicorn server_render:app`

**Environment Variables:**
- **Add Environment Variable**
- **Key:** `DATABASE_URL`
- **Value:** вставь Internal Database URL из шага 5

- **Create Web Service**

### 7. Деплой
Подожди 2–5 минут. Статус станет **Live**.

Скопируй URL, например: `https://psylocyba-license.onrender.com`

---

## Часть 3: Приложение

### 8. Обнови app.py
```python
LICENSE_SERVER_URL = "https://psylocyba-license.onrender.com"
```
(подставь свой URL)

### 9. Пересобери exe
```
build_exe.bat
```

### 10. Добавь ключи
```
cd license_server
python add_key_remote.py https://psylocyba-license.onrender.com XXXX-XXXX-XXXX
```
или
```
python generate_keys_remote.py https://psylocyba-license.onrender.com 10
```

---

## Готово

Дай другу новый exe и ключ. Работает без VPN.
