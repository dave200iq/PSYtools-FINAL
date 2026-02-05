# Сборка Psylocyba Tools (Mac + Windows) через GitHub Actions

## Как использовать

1. **Push** в ветку `main` или `master` — автоматически собираются **обе версии** (Mac и Windows).

2. **Скачать результат:**
   - GitHub → **Actions** → выберите завершённый workflow **Build (Mac + Windows)**.
   - Внизу в **Artifacts** будут:
     - **Psylocyba_Tools-Mac** — для macOS (.app)
     - **Psylocyba_Tools-Windows** — для Windows (.exe)

3. **На Mac:** распакуйте ZIP, перетащите `Psylocyba_Tools.app` в Applications.

4. **На Windows:** распакуйте ZIP, запустите `Psylocyba_Tools.exe`.

## Важно

- `config.json` в `.gitignore` — API-ключи не попадают в репо.
- Для приватного репо: 2000 минут GitHub Actions в месяц бесплатно.
