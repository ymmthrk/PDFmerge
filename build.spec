# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for PDFmerge
Windows用単一exeファイルを生成
"""

import sys
import os
from pathlib import Path

block_cipher = None

# srcディレクトリをパスに追加
src_path = os.path.abspath('src')

a = Analysis(
    ['src/main.py'],
    pathex=[src_path],
    binaries=[],
    datas=[
        ('src/ui', 'ui'),
        ('src/core', 'core'),
        ('src/version.py', '.'),
    ],
    hiddenimports=[
        'pikepdf',
        'pikepdf._core',
        'PIL',
        'PIL.Image',
        'fitz',
        'fitz.fitz',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'pandas',
        'scipy',
        'cv2',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PDFmerge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    version='version_info.txt',
)
