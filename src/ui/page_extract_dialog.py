#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ページ抽出ダイアログ
"""

from typing import List

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QGroupBox, QCheckBox, QListWidget, QListWidgetItem,
    QAbstractItemView
)
from PySide6.QtCore import Qt

from core.pdf_info import PDFInfo


class PageExtractDialog(QDialog):
    """ページ抽出ダイアログ"""

    def __init__(self, pdf_info: PDFInfo, parent=None):
        super().__init__(parent)
        self.pdf_info = pdf_info
        self.selected_pages: List[int] = []

        self.setWindowTitle(f"ページ抽出 - {pdf_info.filename}")
        self.setMinimumSize(450, 550)
        self.resize(500, 600)
        self._setup_ui()
        self._load_pages()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 説明
        info_label = QLabel(f"抽出するページを選択してください（全{self.pdf_info.page_count}ページ）")
        info_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(info_label)

        # 範囲指定
        range_group = QGroupBox("範囲指定")
        range_layout = QHBoxLayout(range_group)

        self.range_input = QLineEdit()
        self.range_input.setPlaceholderText("例: 1-3, 5, 7-10")
        range_layout.addWidget(self.range_input)

        apply_btn = QPushButton("選択に反映")
        apply_btn.clicked.connect(self._apply_range)
        range_layout.addWidget(apply_btn)

        layout.addWidget(range_group)

        # ページリスト（チェックボックス付き）
        list_label = QLabel("または個別に選択:")
        layout.addWidget(list_label)

        self.page_list = QListWidget()
        self.page_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.page_list.setIconSize(Qt.QSize(60, 80))
        self.page_list.setSpacing(2)
        layout.addWidget(self.page_list)

        # 選択ボタン
        select_btn_layout = QHBoxLayout()

        select_all_btn = QPushButton("全選択")
        select_all_btn.clicked.connect(self._select_all)
        select_btn_layout.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("全解除")
        deselect_all_btn.clicked.connect(self._deselect_all)
        select_btn_layout.addWidget(deselect_all_btn)

        select_odd_btn = QPushButton("奇数ページ")
        select_odd_btn.clicked.connect(self._select_odd)
        select_btn_layout.addWidget(select_odd_btn)

        select_even_btn = QPushButton("偶数ページ")
        select_even_btn.clicked.connect(self._select_even)
        select_btn_layout.addWidget(select_even_btn)

        select_btn_layout.addStretch()
        layout.addLayout(select_btn_layout)

        # 選択数表示
        self.count_label = QLabel("0 ページ選択中")
        self.count_label.setStyleSheet("color: #0078d4; font-weight: bold;")
        layout.addWidget(self.count_label)

        # ダイアログボタン
        dialog_btn_layout = QHBoxLayout()
        dialog_btn_layout.addStretch()

        cancel_btn = QPushButton("キャンセル")
        cancel_btn.clicked.connect(self.reject)
        dialog_btn_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("抽出")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self._on_ok)
        dialog_btn_layout.addWidget(ok_btn)

        layout.addLayout(dialog_btn_layout)

        # 選択変更時のシグナル
        self.page_list.itemSelectionChanged.connect(self._update_count)

    def _load_pages(self):
        """ページを読み込み"""
        self.page_list.clear()

        for page_idx in range(self.pdf_info.page_count):
            item = QListWidgetItem()

            # サムネイル取得
            pixmap = self.pdf_info.get_thumbnail(page_idx, 60)
            if pixmap:
                from PySide6.QtGui import QIcon
                icon = QIcon(pixmap)
                item.setIcon(icon)

            # ラベル
            rotation = self.pdf_info.page_rotations.get(page_idx, 0)
            label = f"ページ {page_idx + 1}"
            if rotation:
                label += f" (🔄{rotation}°)"
            item.setText(label)

            item.setData(Qt.UserRole, page_idx)
            self.page_list.addItem(item)

    def _parse_range(self, text: str) -> List[int]:
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
                        if 0 <= i < self.pdf_info.page_count and i not in pages:
                            pages.append(i)
                except ValueError:
                    continue
            else:
                try:
                    idx = int(part) - 1
                    if 0 <= idx < self.pdf_info.page_count and idx not in pages:
                        pages.append(idx)
                except ValueError:
                    continue

        return sorted(pages)

    def _apply_range(self):
        """範囲指定を選択に反映"""
        pages = self._parse_range(self.range_input.text())
        self.page_list.clearSelection()
        for page_idx in pages:
            self.page_list.item(page_idx).setSelected(True)

    def _select_all(self):
        """全選択"""
        self.page_list.selectAll()

    def _deselect_all(self):
        """全解除"""
        self.page_list.clearSelection()

    def _select_odd(self):
        """奇数ページ選択"""
        self.page_list.clearSelection()
        for i in range(0, self.pdf_info.page_count, 2):
            self.page_list.item(i).setSelected(True)

    def _select_even(self):
        """偶数ページ選択"""
        self.page_list.clearSelection()
        for i in range(1, self.pdf_info.page_count, 2):
            self.page_list.item(i).setSelected(True)

    def _update_count(self):
        """選択数を更新"""
        count = len(self.page_list.selectedItems())
        self.count_label.setText(f"{count} ページ選択中")

    def _on_ok(self):
        """OKボタン押下"""
        self.selected_pages = []
        for item in self.page_list.selectedItems():
            self.selected_pages.append(item.data(Qt.UserRole))
        self.selected_pages.sort()

        if not self.selected_pages:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "警告", "ページを1つ以上選択してください。")
            return

        self.accept()

    def get_selected_pages(self) -> List[int]:
        """選択されたページを取得"""
        return self.selected_pages
