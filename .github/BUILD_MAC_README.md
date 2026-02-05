# Сборка Psylocyba Tools для macOS через GitHub Actions

## Как использовать

1. **Создайте репозиторий** на GitHub (можно приватный).

2. **Загрузите проект** в репозиторий:
   ```bash
   cd "C:\Users\dave2\OneDrive\Рабочий стол\Psylocyba_Tools"
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/ВАШ_ЛОГИН/Psylocyba_Tools.git
   git push -u origin main
   ```
   (Если основная ветка — `master`, измените в команде.)

3. **Запуск сборки:**
   - При каждом `git push` в ветку `main`/`master` сборка запускается автоматически.
   - Либо: GitHub → вкладка **Actions** → **Build Mac** → **Run workflow** (ручной запуск).

4. **Скачать результат:**
   - GitHub → **Actions** → выберите завершённый workflow.
   - Внизу страницы в разделе **Artifacts** нажмите **Psylocyba_Tools-Mac**.
   - Скачается архив `Psylocyba_Tools-Mac.zip` с `Psylocyba_Tools.app` внутри.

5. **На Mac:** распакуйте ZIP, перетащите `Psylocyba_Tools.app` в «Программы» (Applications) и запустите.

## Важно

- Перед push добавьте `config.json` в `.gitignore`, если в нём хранятся API-ключи.
- Для приватного репозитория бесплатно доступно 2000 минут GitHub Actions в месяц.
