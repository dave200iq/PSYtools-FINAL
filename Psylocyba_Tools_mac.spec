# -*- mode: python ; coding: utf-8 -*-
# Mac .app bundle (onedir, windowed)
import os
import sys
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
    cipher=block_cipher, noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz, a.scripts, [],
    name='Psylocyba_Tools',
    debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
    console=False,  # windowed
)
coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=False, upx=False, upx_exclude=[], name='Psylocyba_Tools',
)
# macOS .app bundle (only when building on Mac)
if sys.platform == 'darwin':
    app = BUNDLE(coll, name='Psylocyba_Tools.app', icon=None, bundle_identifier='com.psylocyba.tools')
