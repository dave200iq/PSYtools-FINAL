# -*- coding: utf-8 -*-
"""
Скрипт один раз создаёт папки assets/fonts, assets/icons, assets/flags,
скачивает шрифт Inter и генерирует иконки и флаги для Psylocyba Tools.
Запуск: python create_assets.py
"""
import os
import sys
import zipfile
import urllib.request
from pathlib import Path

# Корень проекта — там же, где app.py
APP_DIR = Path(__file__).resolve().parent
ASSETS = APP_DIR / "assets"
FONTS_DIR = ASSETS / "fonts"
ICONS_DIR = ASSETS / "icons"
FLAGS_DIR = ASSETS / "flags"


def main():
    for d in (FONTS_DIR, ICONS_DIR, FLAGS_DIR):
        d.mkdir(parents=True, exist_ok=True)
        print("OK:", d)

    # ---------- Скачать шрифт Inter ----------
    inter_zip = FONTS_DIR / "Inter.zip"
    if not (FONTS_DIR / "Inter-Regular.ttf").exists():
        print("Downloading Inter font...")
        try:
            urllib.request.urlretrieve(
                "https://github.com/rsms/inter/releases/download/v4.1/Inter-4.1.zip",
                inter_zip
            )
            with zipfile.ZipFile(inter_zip, "r") as z:
                for name in z.namelist():
                    if name.endswith(".ttf") and "Inter-" in name and "Display" not in name:
                        base = os.path.basename(name)
                        if base in ("Inter-Regular.ttf", "Inter-Medium.ttf", "Inter-SemiBold.ttf", "Inter-Bold.ttf"):
                            with z.open(name) as src:
                                (FONTS_DIR / base).write_bytes(src.read())
                            print("  ", base)
            inter_zip.unlink(missing_ok=True)
        except Exception as e:
            print("Font download error:", e)
    else:
        print("Inter font already in", FONTS_DIR)

    # ---------- Иконки и флаги (Pillow) ----------
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("Install Pillow: pip install Pillow")
        return

    def save_icon(name, draw_fn, size=64):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw_fn(ImageDraw.Draw(img), size)
        img.save(ICONS_DIR / name)
        print("Icon:", name)

    # Ключ
    def draw_key(d, s):
        cx, cy = s // 2, s // 2
        d.ellipse([cx - 16, cy - 16, cx, cy], outline="#fff", width=3)
        d.rounded_rectangle([cx - 4, cy - 8, cx + 22, cy - 2], radius=2, fill="#fff")
        d.rectangle([cx + 14, cy - 2, cx + 20, cy + 5], fill="#fff")
        d.rectangle([cx + 6, cy - 2, cx + 12, cy + 4], fill="#fff")

    # QR
    def draw_qr(d, s):
        p, bs = 10, 7
        for (ox, oy) in [(p, p), (s - p - bs * 3, p), (p, s - p - bs * 3)]:
            d.rectangle([ox, oy, ox + bs * 3, oy + bs * 3], outline="#fff", width=3)
            d.rectangle([ox + bs, oy + bs, ox + bs * 2, oy + bs * 2], fill="#fff")
        for (ox, oy) in [(s // 2, s // 2), (s // 2 + bs, s // 2 + bs), (s - p - bs, s - p - bs)]:
            d.rectangle([ox - 2, oy - 2, ox + 3, oy + 3], fill="#fff")

    # Обновить
    def draw_refresh(d, s):
        cx, cy = s // 2, s // 2
        r = 18
        d.arc([cx - r, cy - r, cx + r, cy + r], start=40, end=320, fill="#fff", width=4)
        ax, ay = cx + r - 4, cy - r + 4
        d.polygon([(ax - 6, ay - 2), (ax + 2, ay - 8), (ax + 2, ay + 4)], fill="#fff")

    # Корзина
    def draw_trash(d, s):
        cx, cy = s // 2, s // 2
        d.rounded_rectangle([cx - 14, cy - 14, cx + 14, cy - 9], radius=2, fill="#fff")
        d.rounded_rectangle([cx - 6, cy - 18, cx + 6, cy - 14], radius=2, fill="#fff")
        d.rounded_rectangle([cx - 12, cy - 8, cx + 12, cy + 18], radius=3, fill="#fff")
        for x in [cx - 5, cx, cx + 5]:
            d.line([(x, cy - 3), (x, cy + 13)], fill=(15, 13, 22), width=2)

    # Инфо
    def draw_info(d, s):
        cx, cy = s // 2, s // 2
        r = 20
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline="#8b8699", width=2)
        d.rounded_rectangle([cx - 2, cy - 2, cx + 3, cy + 10], radius=1, fill="#8b8699")
        d.ellipse([cx - 3, cy - 10, cx + 3, cy - 4], fill="#8b8699")

    save_icon("key.png", draw_key)
    save_icon("qr.png", draw_qr)
    save_icon("refresh.png", draw_refresh)
    save_icon("trash.png", draw_trash)
    save_icon("info.png", draw_info)

    # ---------- Флаги ----------
    w, h = 96, 64

    # Россия
    ru = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dr = ImageDraw.Draw(ru)
    stripe = h // 3
    dr.rectangle([0, 0, w, stripe], fill=(255, 255, 255))
    dr.rectangle([0, stripe, w, stripe * 2], fill=(0, 57, 166))
    dr.rectangle([0, stripe * 2, w, h], fill=(213, 43, 30))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=8, fill=255)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(ru, (0, 0), mask)
    ImageDraw.Draw(out).rounded_rectangle([0, 0, w - 1, h - 1], radius=8, outline=(60, 60, 80), width=1)
    out.save(FLAGS_DIR / "ru.png")
    print("Flag: ru.png")

    # UK (упрощённо)
    gb = Image.new("RGBA", (w, h), (0, 36, 125))
    dg = ImageDraw.Draw(gb)
    dg.rectangle([0, 0, w, h], outline=(0, 36, 125))
    dg.line([(0, 0), (w, h)], fill="white", width=10)
    dg.line([(w, 0), (0, h)], fill="white", width=10)
    dg.line([(0, 0), (w, h)], fill=(200, 16, 46), width=5)
    dg.line([(w, 0), (0, h)], fill=(200, 16, 46), width=5)
    dg.rectangle([w // 2 - 7, 0, w // 2 + 7, h], fill="white")
    dg.rectangle([0, h // 2 - 5, w, h // 2 + 5], fill="white")
    dg.rectangle([w // 2 - 4, 0, w // 2 + 4, h], fill=(200, 16, 46))
    dg.rectangle([0, h // 2 - 3, w, h // 2 + 3], fill=(200, 16, 46))
    mask2 = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask2).rounded_rectangle([0, 0, w - 1, h - 1], radius=8, fill=255)
    out2 = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out2.paste(gb, (0, 0), mask2)
    ImageDraw.Draw(out2).rounded_rectangle([0, 0, w - 1, h - 1], radius=8, outline=(60, 60, 80), width=1)
    out2.save(FLAGS_DIR / "gb.png")
    print("Flag: gb.png")

    print("\nDone. Assets in:", ASSETS)


if __name__ == "__main__":
    main()
