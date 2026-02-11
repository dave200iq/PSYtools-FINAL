Здесь хранятся ресурсы приложения Psylocyba Tools.

Если папок fonts, icons, flags нет или они пустые:
  1. Запустите в корне проекта файл: Создать_ресурсы.bat
  или
  2. В терминале из папки проекта: python create_assets.py

После этого появятся:
  assets/fonts/   — шрифт Inter (Inter-Regular.ttf и др.)
  assets/icons/   — иконки кнопок (key.png, qr.png, refresh.png, trash.png, info.png)
  assets/flags/    — флаги для выбора языка (ru.png, gb.png)

Требуется: Python, пакет Pillow (pip install Pillow).
