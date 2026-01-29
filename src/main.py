#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDFmerge - PDF結合ツール
ローカルで動作する安全なPDF結合アプリケーション
"""

import sys
import os
from pathlib import Path

# PyInstaller用: srcディレクトリをパスに追加
if getattr(sys, 'frozen', False):
    # exe実行時
    base_path = sys._MEIPASS
else:
    # 通常実行時
    base_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, base_path)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ui.main_window import MainWindow


def main():
    """アプリケーションのエントリーポイント"""
    # High DPI対応
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("PDFmerge")
    app.setApplicationVersion("1.0.0")

    # 日本語フォント設定
    font = QFont()
    font.setFamilies(["Yu Gothic UI", "Meiryo", "Noto Sans CJK JP", "sans-serif"])
    font.setPointSize(10)
    app.setFont(font)

    # スタイル設定
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
