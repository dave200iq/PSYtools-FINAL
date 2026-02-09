# Psylocyba Tools

Desktop app for Telegram (Windows + macOS): clone groups/channels, export members, stats, mass messaging. Modern GUI with license key protection.

## Features

- **Clone Group** — Full copy of a Telegram group (messages, topics, avatar)
- **Clone Channel** — Copy a channel with all posts
- **Export Subscribers** — Export member list to a file
- **Stats** — Get basic channel/group stats
- **Mass Send** — Send messages with delay control
- Modern UI with EN/RU language support
- License key activation (one key per computer)
- Built-in API setup guide

## Download (end users)

- Open the **Releases** page and download:
  - `Psylocyba_Tools-Windows.zip`
  - `Psylocyba_Tools-Mac.zip`

**Требования:** macOS 10.15+ / Windows 10/11

## Quick Start

1. **Run** the app
2. **Activate** — enter your license key when prompted
3. **API Setup** — get **API ID** and **API Hash** from [my.telegram.org](https://my.telegram.org)
4. **Authorize**
   - Default: enter phone + code from Telegram (and 2FA password if enabled)
   - If code doesn’t arrive: use **QR Auth** (Telegram → Settings → Devices → Link Desktop Device)
5. Use the tabs to clone/export/stats/mass send

## Notes / Limitations (Telegram)

Telegram API does **not** allow a perfect “bit‑for‑bit” clone of everything. Depending on permissions and chat settings, some items may not be fully reproducible (e.g. service messages, reactions/views, certain interactive elements).  
Also, Telegram rate limits apply — large operations may take time and can trigger FloodWait.

## For Developers

### Run from source

```bash
pip install -r requirements.txt
python app.py
```

### Build executable (local)

```bash
build_exe.bat
```

Output: `dist/Psylocyba_Tools.exe`

### Build releases (CI)

This repo includes GitHub Actions workflow **Build (Mac + Windows)**:
- Builds Windows + macOS artifacts
- Uploads `Psylocyba_Tools-Windows.zip` and `Psylocyba_Tools-Mac.zip` to a Release

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

## Security / Secrets

Do **not** commit:
- `config.json` (API Hash + phone)
- `.license` (license binding)
- `*.session*` (Telegram sessions)

They are excluded in `.gitignore` by default.

## Telegram

[Channel](https://t.me/+A0Qr2usbsX41YmJi)
