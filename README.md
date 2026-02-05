# Psylocyba Tools

Windows desktop app for Telegram: clone groups and channels, export subscribers. Modern GUI with license key protection.

## Features

- **Clone Group** — Full copy of a Telegram group (messages, topics, avatar)
- **Clone Channel** — Copy a channel with all posts
- **Export Subscribers** — Export member list to a file
- Modern UI with EN/RU language support
- License key activation (one key per computer)
- Built-in API setup guide

## Download

**[→ Скачать Mac и Windows](https://github.com/dave200iq/PSYtools-Releases/releases)** — только приложения, без кода.

**Требования:** macOS 10.15+ / Windows 10/11

## Quick Start

1. **Run** `Psylocyba_Tools.exe`
2. **Activate** — Enter your license key when prompted
3. **API Setup** — Get API ID and API Hash from [my.telegram.org](https://my.telegram.org)
4. **Authorize** — Enter your phone number and the code from Telegram
5. Use the tabs to clone or export

## For Developers

### Run from source

```bash
pip install -r requirements.txt
python app.py
```

### Build executable

```bash
build_exe.bat
```

Output: `dist/Psylocyba_Tools.exe`

### Project structure

```
├── app.py              # Main GUI application
├── scripts/            # Telegram scripts (clone, export)
├── license_server/     # License verification server
├── installer/          # Inno Setup installer config
└── build_exe.bat       # Build script
```

## License Server

The app requires a license server for activation. See `license_server/README.md` for self-hosting instructions.

## Telegram

[Channel](https://t.me/+A0Qr2usbsX41YmJi)
