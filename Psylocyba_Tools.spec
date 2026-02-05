# -*- mode: python ; coding: utf-8 -*-
import os
try:
    SPEC_DIR = os.path.dirname(os.path.abspath(SPEC))
except NameError:
    SPEC_DIR = os.getcwd()
scripts_src = os.path.join(SPEC_DIR, 'scripts')
block_cipher = None

a = Analysis(
    [os.path.join(SPEC_DIR, 'app.py')],
    pathex=[SPEC_DIR],
    binaries=[],
    datas=[(scripts_src, 'scripts')],
    hiddenimports=['telethon', 'customtkinter', 'PIL', 'cryptg', 'rsa'],
    hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[],
    win_no_prefer_redirects=False, win_private_assemblies=False,
    cipher=block_cipher, noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],
    name='Psylocyba_Tools',
    debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
    upx_exclude=[], runtime_tmpdir=None, console=False,
)
