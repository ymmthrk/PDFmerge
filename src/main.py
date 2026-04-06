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

from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor

from version import VERSION, APP_NAME, COPYRIGHT, DESCRIPTION


def _create_splash_pixmap(device_pixel_ratio: float) -> QPixmap:
    """スプラッシュスクリーン用の画像をプログラムで生成（High DPI対応）"""
    # 論理サイズ
    w, h = 360, 180

    # 物理ピクセルサイズで描画し、devicePixelRatioを設定
    pw = int(w * device_pixel_ratio)
    ph = int(h * device_pixel_ratio)
    pixmap = QPixmap(pw, ph)
    pixmap.setDevicePixelRatio(device_pixel_ratio)
    pixmap.fill(QColor("#f0f4f8"))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    # 以降は論理座標で描画（devicePixelRatioが自動適用される）

    # アクセントライン（上部）
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor("#0078d4"))
    painter.drawRect(0, 0, w, 4)

    # アプリ名（上から50pxの位置）
    painter.setFont(QFont("Yu Gothic UI", 22, QFont.Bold))
    painter.setPen(QColor("#1a1a1a"))
    painter.drawText(QRect(0, 35, w, 45), Qt.AlignCenter, APP_NAME)

    # サブタイトル（アプリ名の下）
    painter.setFont(QFont("Yu Gothic UI", 10))
    painter.setPen(QColor("#666666"))
    painter.drawText(QRect(0, 85, w, 25), Qt.AlignCenter, DESCRIPTION)

    # 読み込み中（下部左寄せ）
    painter.setFont(QFont("Yu Gothic UI", 9))
    painter.setPen(QColor("#0078d4"))
    painter.drawText(QRect(12, h - 30, 200, 20), Qt.AlignLeft | Qt.AlignVCenter, "読み込み中...")

    # バージョン（下部右寄せ）
    painter.setPen(QColor("#999999"))
    painter.drawText(QRect(w - 110, h - 30, 100, 20), Qt.AlignRight | Qt.AlignVCenter, f"v{VERSION}")

    painter.end()
    return pixmap


def main():
    """アプリケーションのエントリーポイント"""
    # High DPI対応
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(VERSION)

    # スプラッシュスクリーンを即座に表示
    ratio = app.primaryScreen().devicePixelRatio() if app.primaryScreen() else 1.0
    splash = QSplashScreen(_create_splash_pixmap(ratio))
    splash.show()
    app.processEvents()

    # 日本語フォント設定
    font = QFont()
    font.setFamilies(["Yu Gothic UI", "Meiryo", "Noto Sans CJK JP", "sans-serif"])
    font.setPointSize(10)
    app.setFont(font)

    # スタイル設定
    app.setStyle("Fusion")

    # メインウィンドウの生成（重い処理はここで発生）
    from ui.main_window import MainWindow
    window = MainWindow()
    window.show()

    splash.finish(window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
