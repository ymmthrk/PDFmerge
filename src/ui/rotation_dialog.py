#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回転ダイアログ
"""

from typing import List, Tuple, Dict

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QButtonGroup, QGroupBox, QLineEdit
)
from PySide6.QtCore import Qt


class RotationDialog(QDialog):
    """ページ回転設定ダイアログ"""

    def __init__(self, page_count: int, current_rotations: Dict[int, int] = None, parent=None):
        super().__init__(parent)
        self.page_count = page_count
        self.current_rotations = current_rotations or {}
        self.result_pages: List[int] = []
        self.result_degrees: int = 0
        self.is_reset: bool = False

        self.setWindowTitle("ページ回転")
        self.setMinimumWidth(380)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # 現在の回転状態
        if self.current_rotations:
            info_label = QLabel(f"現在 {len(self.current_rotations)} ページが回転済み")
            info_label.setStyleSheet("color: #0078d4; font-weight: bold;")
            layout.addWidget(info_label)

        # 対象選択
        target_group = QGroupBox("回転対象")
        target_layout = QVBoxLayout(target_group)

        self.target_button_group = QButtonGroup(self)

        self.all_pages_radio = QRadioButton(f"全ページ ({self.page_count}ページ)")
        self.all_pages_radio.setChecked(True)
        self.target_button_group.addButton(self.all_pages_radio, 0)
        target_layout.addWidget(self.all_pages_radio)

        self.range_radio = QRadioButton("ページ範囲指定:")
        self.target_button_group.addButton(self.range_radio, 1)

        range_layout = QHBoxLayout()
        range_layout.addWidget(self.range_radio)

        self.range_input = QLineEdit()
        self.range_input.setPlaceholderText("例: 1-3, 5, 7-10")
        self.range_input.setEnabled(False)
        range_layout.addWidget(self.range_input)
        target_layout.addLayout(range_layout)

        self.range_radio.toggled.connect(self.range_input.setEnabled)

        layout.addWidget(target_group)

        # 回転方向
        direction_group = QGroupBox("回転方向")
        direction_layout = QVBoxLayout(direction_group)

        self.direction_button_group = QButtonGroup(self)

        self.rotate_right = QRadioButton("90° 右回転 (時計回り)")
        self.rotate_right.setChecked(True)
        self.direction_button_group.addButton(self.rotate_right, 90)
        direction_layout.addWidget(self.rotate_right)

        self.rotate_left = QRadioButton("90° 左回転 (反時計回り)")
        self.direction_button_group.addButton(self.rotate_left, -90)
        direction_layout.addWidget(self.rotate_left)

        self.rotate_180 = QRadioButton("180° 回転")
        self.direction_button_group.addButton(self.rotate_180, 180)
        direction_layout.addWidget(self.rotate_180)

        self.rotate_reset = QRadioButton("回転をリセット (0°に戻す)")
        self.rotate_reset.setStyleSheet("color: #cc0000;")
        self.direction_button_group.addButton(self.rotate_reset, 0)
        direction_layout.addWidget(self.rotate_reset)

        layout.addWidget(direction_group)

        # ボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("キャンセル")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("適用")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self._on_ok)
        button_layout.addWidget(ok_btn)

        layout.addLayout(button_layout)

    def _parse_page_range(self, text: str) -> List[int]:
        """ページ範囲文字列をパース"""
        pages = []
        parts = text.replace(" ", "").split(",")

        for part in parts:
            if "-" in part:
                try:
                    start, end = part.split("-")
                    start_idx = int(start) - 1
                    end_idx = int(end) - 1
                    for i in range(start_idx, end_idx + 1):
                        if 0 <= i < self.page_count and i not in pages:
                            pages.append(i)
                except ValueError:
                    continue
            else:
                try:
                    idx = int(part) - 1
                    if 0 <= idx < self.page_count and idx not in pages:
                        pages.append(idx)
                except ValueError:
                    continue

        return sorted(pages)

    def _on_ok(self):
        """OKボタン押下時"""
        # 対象ページ
        if self.all_pages_radio.isChecked():
            self.result_pages = list(range(self.page_count))
        else:
            self.result_pages = self._parse_page_range(self.range_input.text())
            if not self.result_pages:
                self.result_pages = list(range(self.page_count))

        # 回転角度
        self.result_degrees = self.direction_button_group.checkedId()
        self.is_reset = self.rotate_reset.isChecked()

        self.accept()

    def get_result(self) -> Tuple[List[int], int, bool]:
        """結果を取得: (対象ページリスト, 回転角度, リセットフラグ)"""
        return self.result_pages, self.result_degrees, self.is_reset
