#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
パスワード入力ダイアログ
"""

from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit
)
from PySide6.QtCore import Qt


class PasswordDialog(QDialog):
    """パスワード入力ダイアログ"""

    def __init__(self, filename: str, parent=None):
        super().__init__(parent)
        self.filename = filename
        self._password: Optional[str] = None

        self.setWindowTitle("パスワード入力")
        self.setMinimumWidth(400)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # アイコンとメッセージ
        header_layout = QHBoxLayout()

        lock_label = QLabel("🔒")
        lock_label.setStyleSheet("font-size: 32px;")
        header_layout.addWidget(lock_label)

        message_layout = QVBoxLayout()
        message_layout.setSpacing(4)

        title_label = QLabel("パスワードで保護されています")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        message_layout.addWidget(title_label)

        filename_label = QLabel(self.filename)
        filename_label.setStyleSheet("color: #666666; font-size: 12px;")
        filename_label.setWordWrap(True)
        message_layout.addWidget(filename_label)

        header_layout.addLayout(message_layout)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # パスワード入力欄
        password_layout = QHBoxLayout()

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("パスワードを入力")
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #0078d4;
            }
        """)
        self.password_input.returnPressed.connect(self._on_ok)
        password_layout.addWidget(self.password_input)

        # 表示/非表示切り替えボタン
        self.toggle_btn = QPushButton("👁")
        self.toggle_btn.setFixedSize(36, 36)
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: #f5f5f5;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
            }
            QPushButton:checked {
                background-color: #d0e8ff;
                border-color: #0078d4;
            }
        """)
        self.toggle_btn.clicked.connect(self._toggle_password_visibility)
        password_layout.addWidget(self.toggle_btn)

        layout.addLayout(password_layout)

        # ボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("キャンセル")
        cancel_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: #f5f5f5;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("OK")
        ok_btn.setDefault(True)
        ok_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                border: none;
                border-radius: 4px;
                background-color: #0078d4;
                color: white;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
        """)
        ok_btn.clicked.connect(self._on_ok)
        button_layout.addWidget(ok_btn)

        layout.addLayout(button_layout)

        # フォーカス設定
        self.password_input.setFocus()

    def _toggle_password_visibility(self):
        """パスワード表示/非表示を切り替え"""
        if self.toggle_btn.isChecked():
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)

    def _on_ok(self):
        """OKボタン押下"""
        self._password = self.password_input.text()
        self.accept()

    def get_password(self) -> Optional[str]:
        """入力されたパスワードを取得"""
        return self._password
