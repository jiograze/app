# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Ana uygulama analizi
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config/config_sample.yaml', 'config'),
        ('templates/*', 'templates'),
    ],
    hiddenimports=[
        'PyQt5.QtCore',
        'PyQt5.QtGui', 
        'PyQt5.QtWidgets',
        'sentence_transformers',
        'transformers',
        'torch',
        'numpy',
        'sklearn',
        'faiss',
        'watchdog',
        'yaml',
        'sqlite3',
        'hashlib',
        'pathlib',
        'threading',
        'queue',
        'logging.handlers',
        'reportlab',
        'PIL',
        'pytesseract'
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib.backends.backend_tkagg',
        'jupyter',
        'IPython'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# PYZ dosyası
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# EXE dosyası (OneDir mode - daha hızlı açılış)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MevzuatSistemi',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI uygulaması için False
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='config/app_icon.ico'  # Varsa uygulama ikonu
)

# COLLECT (OneDir için gerekli)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MevzuatSistemi'
)

# OneFile versiyonu için (yorumda)
"""
exe_onefile = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MevzuatSistemi',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='config/app_icon.ico'
)
"""
