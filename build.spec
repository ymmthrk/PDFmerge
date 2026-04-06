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
        'fitz',
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
        # 未使用のPySide6サブモジュール（QtCore/QtGui/QtWidgets以外）
        'PySide6.Qt3DAnimation',
        'PySide6.Qt3DCore',
        'PySide6.Qt3DExtras',
        'PySide6.Qt3DInput',
        'PySide6.Qt3DLogic',
        'PySide6.Qt3DRender',
        'PySide6.QtAxContainer',
        'PySide6.QtBluetooth',
        'PySide6.QtCharts',
        'PySide6.QtConcurrent',
        'PySide6.QtDBus',
        'PySide6.QtDataVisualization',
        'PySide6.QtDesigner',
        'PySide6.QtGraphs',
        'PySide6.QtGraphsWidgets',
        'PySide6.QtHelp',
        'PySide6.QtHttpServer',
        'PySide6.QtLocation',
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',
        'PySide6.QtNetwork',
        'PySide6.QtNetworkAuth',
        'PySide6.QtNfc',
        'PySide6.QtOpenGL',
        'PySide6.QtOpenGLWidgets',
        'PySide6.QtPdf',
        'PySide6.QtPdfWidgets',
        'PySide6.QtPositioning',
        'PySide6.QtPrintSupport',
        'PySide6.QtQml',
        'PySide6.QtQuick',
        'PySide6.QtQuick3D',
        'PySide6.QtQuickControls2',
        'PySide6.QtQuickTest',
        'PySide6.QtQuickWidgets',
        'PySide6.QtRemoteObjects',
        'PySide6.QtScxml',
        'PySide6.QtSensors',
        'PySide6.QtSerialBus',
        'PySide6.QtSerialPort',
        'PySide6.QtSpatialAudio',
        'PySide6.QtSql',
        'PySide6.QtStateMachine',
        'PySide6.QtSvg',
        'PySide6.QtSvgWidgets',
        'PySide6.QtTest',
        'PySide6.QtTextToSpeech',
        'PySide6.QtUiTools',
        'PySide6.QtWebChannel',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineQuick',
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebSockets',
        'PySide6.QtWebView',
        'PySide6.QtXml',
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
